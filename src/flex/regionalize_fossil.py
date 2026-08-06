"""Reusable fossil-CO2 regionalization / sectoral splitting.

This module factors the tail-end of ``notebooks/5191_extension.py`` (the part
that disaggregates removals, computes gross-positive emissions, extends the
CDR / gross-positive trajectories to the extension end year, splits the global
fossil CO2 over regions and sectors and stitches the result onto history) into
reusable functions.

It is used in two places:

* ``5191_extension.py`` calls :func:`regionalize_fossil_co2` with the storyline
  fossil-CO2 extension (behaviour identical to before).
* ``5196_apply_optimised.py`` calls :func:`load_regionalization_inputs` followed
  by :func:`regionalize_fossil_co2` with the *optimised* fossil-CO2 trajectory to
  produce a regionalised counterfactual emissions file, keeping the original
  non-CO2 and CO2 AFOLU data untouched.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pandas_indexing as pix

from .cdr_and_fossil_splits import (
    add_removals_and_positive_fossil_emissions_to_historical,
    extend_cdr_components_vectorized,
    get_2100_compound_composition_co2,
)
from .config import DATA_DIR, FlexConfig
from .extension_functionality import sigmoid_function
from .finish_regional_extensions import (
    extend_regional_for_missing,
    merge_historical_future_timeseries,
)
from .general_utils_for_extensions import (
    convert_continuous_to_fair_csv,
    fix_up_and_concatenate_extensions,
    fix_year_columns_to_numeric,
    interpolate_to_annual,
)

GROSS_POSITIVE = "Emissions|CO2|Gross Positive Emissions"
GROSS_REMOVALS = "Emissions|CO2|Gross Removals"
FOSSIL_VARIABLE = "Emissions|CO2|Energy and Industrial Processes"

# Gross-positive fossil CO2 sectors. These sum (over sectors and regions) to the
# global gross-positive emissions. The first six are regional-only; the last two
# (Aircraft, International Shipping) are reported at the World level only.
GROSS_POSITIVE_SECTORS = [
    "Emissions|CO2|Energy Sector",
    "Emissions|CO2|Industrial Sector",
    "Emissions|CO2|Transportation Sector",
    "Emissions|CO2|Residential Commercial Other",
    "Emissions|CO2|Solvents Production and Application",
    "Emissions|CO2|Waste",
    "Emissions|CO2|Aircraft",
    "Emissions|CO2|International Shipping",
]

# CDR / removal components. These sum (over components and regions) to the global
# gross removals.
CDR_COMPONENTS = [
    "Emissions|CO2|BECCS",
    "Emissions|CO2|Direct Air Capture",
    "Emissions|CO2|Ocean",
    "Emissions|CO2|Enhanced Weathering",
    "Emissions|CO2|Biochar",
    "Emissions|CO2|Soil Carbon Management",
    "Emissions|CO2|Other CDR",
]


def _disaggregate_removals(scenarios_regional: pd.DataFrame):
    """Extract regional CDR components and the global gross-removals series.

    Mirrors the "Removal disaggregation" cell of 5191.
    """
    co2_beccs = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|BECCS")])
    co2_dacc = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Direct Air Capture")])
    co2_ocean = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Ocean")])
    co2_ew = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Enhanced Weathering")])
    co2_biochar = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Biochar")])
    co2_soil = interpolate_to_annual(
        scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Soil Carbon Management")]
    )
    co2_othercdr = interpolate_to_annual(scenarios_regional.loc[pix.ismatch(variable="Emissions|CO2|Other CDR")])
    co2_ffi = interpolate_to_annual(
        scenarios_regional.loc[
            pix.ismatch(
                variable=FOSSIL_VARIABLE,
                workflow="for_scms",
            )
        ]
    )

    co2_cdr = (
        co2_dacc
        + co2_ocean.values
        + co2_ew.values
        + co2_beccs.values
        + co2_biochar.values
        + co2_soil.values
        + co2_othercdr.values
    )

    # Rename the variable level to "Gross Removals" on the aggregated CDR.
    new_index = []
    for idx_tuple in list(co2_cdr.index):
        new_tuple = list(idx_tuple)
        new_tuple[3] = GROSS_REMOVALS
        new_index.append(tuple(new_tuple))
    co2_cdr.index = pd.MultiIndex.from_tuples(new_index, names=co2_cdr.index.names)

    global_cdr = co2_cdr.groupby(["model", "scenario", "variable", "unit"]).sum()

    cdr_components = {
        "BECCS": co2_beccs,
        "DACCS": co2_dacc,
        "Ocean": co2_ocean,
        "Enhanced_Weathering": co2_ew,
        "Biochar": co2_biochar,
        "Soil_Management": co2_soil,
        "Other_CDR": co2_othercdr,
    }
    return cdr_components, co2_ffi, global_cdr


def _calculate_gross_positive(co2_ffi: pd.DataFrame, global_cdr: pd.DataFrame):
    """Compute global gross-positive emissions = FFI - CDR (per model/scenario)."""
    co2_ffi_grouped = co2_ffi.groupby(["model", "scenario", "variable", "unit"]).sum()

    common_scenarios = []
    for model, scenario, var_cdr, unit in global_cdr.index:
        matching_ffi = co2_ffi_grouped.loc[
            (co2_ffi_grouped.index.get_level_values("model") == model)
            & (co2_ffi_grouped.index.get_level_values("scenario") == scenario)
            & (co2_ffi_grouped.index.get_level_values("unit") == unit)
        ]
        if len(matching_ffi) > 0:
            cdr_data = global_cdr.loc[(model, scenario, var_cdr, unit)]
            ffi_data = matching_ffi.iloc[0]
            combined_data = -cdr_data + ffi_data
            new_index = (model, scenario, GROSS_POSITIVE, unit)
            common_scenarios.append((new_index, combined_data))

    if not common_scenarios:
        return None

    indices, data_rows = zip(*common_scenarios)
    return pd.DataFrame(
        data=list(data_rows),
        index=pd.MultiIndex.from_tuples(indices, names=global_cdr.index.names),
    )


def _extend_gross_positive_and_cdr(
    co2_gross_positive: pd.DataFrame | None,
    global_cdr: pd.DataFrame,
    fossil_extension_df: pd.DataFrame,
    removal_dictionary: dict,
    scenario_model_match: dict,
    scenario_end_year: int,
    extensions_end_year: int,
):
    """Extend gross-positive and global CDR to the extension end year.

    POS strategy: CDR held constant, gross-positive follows the fossil trajectory.
    NEG strategy: gross-positive follows a sigmoid decay, CDR is the residual.
    """
    years_extension = np.arange(scenario_end_year + 1, extensions_end_year + 1)

    if co2_gross_positive is None:
        return None, None

    if co2_gross_positive.loc[:, years_extension].shape[1] == len(years_extension):
        co2_gross_positive_ext = co2_gross_positive
    else:
        extension_cols_gross_pos = pd.DataFrame(np.nan, index=co2_gross_positive.index, columns=years_extension)
        co2_gross_positive_ext = pd.concat([co2_gross_positive, extension_cols_gross_pos], axis=1)

    if global_cdr.loc[:, years_extension].shape[1] == len(years_extension):
        global_cdr_ext = global_cdr
    else:
        extension_cols_cdr = pd.DataFrame(np.nan, index=global_cdr.index, columns=years_extension)
        global_cdr_ext = pd.concat([global_cdr, extension_cols_cdr], axis=1)

    # Map removal strategies (keyed by marker) to scenario names.
    removal_strategy_map = {}
    for marker, info in scenario_model_match.items():
        scenario = info[0]
        if marker in removal_dictionary:
            removal_strategy_map[scenario] = removal_dictionary[marker]

    processed_count = 0
    for idx in co2_gross_positive.index:
        model, scenario, variable, unit = idx

        if scenario not in removal_strategy_map:
            print(f"Scenario {scenario} not in removal_dictionary, skipping.")
            continue

        strategy_info = removal_strategy_map[scenario]
        strategy = strategy_info[0]

        try:
            fossil_row = fossil_extension_df.loc[(model, scenario, "World", FOSSIL_VARIABLE, unit)]
            if isinstance(fossil_row, pd.DataFrame):
                fossil_row = fossil_row.iloc[0]
        except KeyError:
            print(f"No fossil extension for {model}, {scenario}, skipping.")
            continue

        cdr_idx = (model, scenario, GROSS_REMOVALS, unit)
        cdr_2100 = global_cdr.loc[cdr_idx, 2100.0]
        gross_pos_2100 = co2_gross_positive.loc[idx, 2100.0]

        if strategy == "POS":
            cdr_extension = np.full(len(years_extension), cdr_2100)
            fossil_vals = fossil_row[years_extension].values
            gross_pos_extension = fossil_vals - cdr_2100
        elif strategy == "NEG":
            decay_timescale = strategy_info[1]
            offset = strategy_info[2]
            offset_shift = (1.25 * decay_timescale) / 2
            gross_pos_extension = sigmoid_function(
                0,
                gross_pos_2100,
                years_extension[0] + offset - offset_shift,
                years_extension[0] + offset + offset_shift,
                years_extension,
                adjust_from=True,
            )
            fossil_vals = fossil_row[years_extension].values
            cdr_extension = fossil_vals - gross_pos_extension
        else:
            print(f"Unknown strategy {strategy} for scenario {scenario}, skipping.")
            continue

        co2_gross_positive_ext.loc[idx, years_extension] = gross_pos_extension
        global_cdr_ext.loc[cdr_idx, years_extension] = cdr_extension
        processed_count += 1

    print(f"Processed {processed_count} scenario(s) for gross-positive/CDR extension")
    return co2_gross_positive_ext, global_cdr_ext


def _plot_gross_positive_vs_cdr(
    co2_gross_positive_ext: pd.DataFrame,
    global_cdr_ext: pd.DataFrame,
    fossil_extension_df: pd.DataFrame,
    scenario_model_match: dict,
    future_start_year: float,
    plots_dir: Path,
):
    """Diagnostic stacked-area plot of gross-positive vs CDR vs net FFI."""
    import matplotlib.pyplot as plt

    years = sorted(col for col in co2_gross_positive_ext.columns if isinstance(col, int | float))
    years_extension = sorted(col for col in fossil_extension_df.columns if isinstance(col, int | float))
    positive_color = "tab:brown"
    negative_color = "tab:green"

    scenarios_to_plot = []
    for model, scenario, var, unit in co2_gross_positive_ext.index:
        if (model, scenario) not in scenarios_to_plot:
            scenarios_to_plot.append((model, scenario))

    plot_grid_cols = 4
    n_scenarios = len(scenarios_to_plot)
    n_rows = (n_scenarios + plot_grid_cols - 1) // plot_grid_cols

    fig, axes = plt.subplots(n_rows, plot_grid_cols, figsize=(20, 6 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    for i, (model, scenario) in enumerate(scenarios_to_plot):
        ax = axes[i]
        gross_positive_data = co2_gross_positive_ext.loc[(model, scenario, GROSS_POSITIVE, "Mt CO2/yr"), years]
        cdr_data = global_cdr_ext.loc[(model, scenario, GROSS_REMOVALS, "Mt CO2/yr"), years]
        ffi_data = fossil_extension_df.loc[
            (fossil_extension_df.index.get_level_values("model") == model)
            & (fossil_extension_df.index.get_level_values("scenario") == scenario)
            & (fossil_extension_df.index.get_level_values("unit") == "Mt CO2/yr")
        ]
        if len(ffi_data) > 0:
            marker_code = None
            for marker, info in scenario_model_match.items():
                if info[1] == model and info[0] == scenario:
                    marker_code = marker
                    break

            ax.fill_between(years, 0, gross_positive_data.values, alpha=0.6, color=positive_color, label="Gross Positive")
            ax.fill_between(years, 0, cdr_data.values, alpha=0.6, color=negative_color, label="CDR (negative)")
            ax.plot(years_extension, ffi_data.T.values, color="black", linewidth=2, linestyle="-", alpha=0.8, label="Net FFI")
            ax.axvline(x=future_start_year, color="red", linestyle="--", alpha=0.7, linewidth=1)
            ax.axhline(y=0, color="black", linestyle="-", alpha=0.3, linewidth=0.5)
            ax.set_title(f"{marker_code}: {scenario[:30]}...", fontsize=12, fontweight="bold")
            ax.set_xlim(min(years), 2300)
            ax.grid(True, alpha=0.3)
            if i >= plot_grid_cols:
                ax.set_xlabel("Year", fontsize=10)
            if i % plot_grid_cols == 0:
                ax.set_ylabel("CO2 Emissions (Mt CO2/yr)", fontsize=10)
            if i == 0:
                ax.legend(fontsize=9)

    for i in range(len(scenarios_to_plot), len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(
        "Gross Positive vs CDR vs Net FFI Emissions by Scenario\n"
        "Brown = Positive, Green = CDR, Black lines = Net result",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.savefig(Path(plots_dir) / "gross_positive_vs_cdr_vs_ffi_by_scenario.png")
    plt.close(fig)


def regionalize_fossil_co2(
    fossil_extension_df: pd.DataFrame,
    scenarios_regional: pd.DataFrame,
    df_afolu: pd.DataFrame,
    df_all: pd.DataFrame,
    history: pd.DataFrame,
    fractions_fossil_total: dict,
    removal_dictionary: dict,
    scenario_model_match: dict,
    *,
    future_start_year: float,
    scenario_end_year: int,
    extensions_end_year: int,
    make_plots: bool = False,
    plots_dir: Path | None = None,
):
    """Regionalise/sectorise global fossil CO2 and stitch onto history.

    This encapsulates the tail-end of 5191: removal disaggregation, gross
    positive computation, POS/NEG extension to ``extensions_end_year``, regional
    CDR component extension, merging of all components, allocation of the global
    fossil to missing regions, and merging with history.

    Parameters
    ----------
    fossil_extension_df
        Global (World) fossil CO2 extension, variable
        ``"Emissions|CO2|Energy and Industrial Processes"``. In 5191 this is the
        storyline extension; in 5196 it is the optimised counterfactual.
    scenarios_regional, df_afolu, df_all, history
        Regional input data, AFOLU CO2, non-CO2 emissions and history.
    fractions_fossil_total
        2100 sectoral/regional fractions keyed by ``(model, scenario)``.
    removal_dictionary, scenario_model_match
        Per-marker removal strategy and marker -> (scenario, model, color) map.

    Returns
    -------
    (continuous_timeseries_concise, df_everything)
        The history-stitched continuous timeseries and the (future) extensions
        dataframe.
    """
    df_all = fix_year_columns_to_numeric(df_all)
    df_afolu = fix_year_columns_to_numeric(df_afolu)

    cdr_components, co2_ffi, global_cdr = _disaggregate_removals(scenarios_regional)
    co2_gross_positive = _calculate_gross_positive(co2_ffi, global_cdr)

    co2_gross_positive_ext, global_cdr_ext = _extend_gross_positive_and_cdr(
        co2_gross_positive,
        global_cdr,
        fossil_extension_df,
        removal_dictionary,
        scenario_model_match,
        scenario_end_year,
        extensions_end_year,
    )

    if make_plots and co2_gross_positive_ext is not None and plots_dir is not None:
        _plot_gross_positive_vs_cdr(
            co2_gross_positive_ext,
            global_cdr_ext,
            fossil_extension_df,
            scenario_model_match,
            future_start_year,
            plots_dir,
        )

    # Extend the individual regional CDR components, maintaining 2100 ratios.
    if global_cdr_ext is not None:
        extended_cdr_components = extend_cdr_components_vectorized(cdr_components, global_cdr_ext)
        co2_beccs_ext = extended_cdr_components["BECCS"]
        co2_dacc_ext = extended_cdr_components["DACCS"]
        co2_ocean_ext = extended_cdr_components["Ocean"]
        co2_ew_ext = extended_cdr_components["Enhanced_Weathering"]
        co2_biochar_ext = extended_cdr_components["Biochar"]
        co2_soil_ext = extended_cdr_components["Soil_Management"]
        co2_other_cdr_ext = extended_cdr_components["Other_CDR"]
    else:
        co2_beccs_ext = co2_dacc_ext = co2_ocean_ext = co2_ew_ext = None
        co2_biochar_ext = co2_soil_ext = co2_other_cdr_ext = None

    # Merge all extended components into df_everything.
    _merge_dict = {
        "fossil_extension": fossil_extension_df,
        "afolu_extensions": df_afolu,
        "non_co2_extensions": df_all,
        "gross_positive_extensions": co2_gross_positive_ext,
        "cdr_extensions": global_cdr_ext,
        "beccs_extensions": co2_beccs_ext,
        "dacc_extensions": co2_dacc_ext,
        "ocean_extensions": co2_ocean_ext,
        "ew_extensions": co2_ew_ext,
        "biochar_extensions": co2_biochar_ext,
        "soil_extensions": co2_soil_ext,
        "other_cdr_extensions": co2_other_cdr_ext,
    }
    _merge_dict = {k: v for k, v in _merge_dict.items() if v is not None}
    df_everything = fix_up_and_concatenate_extensions(_merge_dict, startyr=future_start_year)

    df_everything = extend_regional_for_missing(df_everything, scenarios_regional, fractions_fossil_total)

    # Drop duplicate metadata rows (CSV preparation only).
    if df_everything.index.duplicated(keep=False).any():
        df_everything = df_everything[~df_everything.index.duplicated(keep="first")]

    # Normalise year columns to float.
    year_cols = [col for col in df_everything.columns if str(col).isdigit()]
    df_everything.rename(columns={col: float(col) for col in year_cols}, inplace=True)

    # Add gross-positive / gross-removals rows to history, then stitch.
    history = add_removals_and_positive_fossil_emissions_to_historical(history)
    continuous_timeseries_concise = merge_historical_future_timeseries(
        history, df_everything, overlap_year=int(future_start_year)
    )

    return continuous_timeseries_concise, df_everything


def rescale_fossil_splits_to_optimised(
    df_everything: pd.DataFrame,
    strategy: str,
) -> pd.DataFrame:
    """Rescale the regional/sectoral fossil CO2 splits to the optimised net EIP.

    After :func:`regionalize_fossil_co2` is called with an *optimised* global
    fossil trajectory, the World ``Emissions|CO2|Energy and Industrial Processes``
    row carries the optimised net EIP, but the gross-positive sectors and CDR
    components are still the base-scenario breakdown (optimisation-aware only in
    the post-2100 extension tail). This function reconciles the breakdown to the
    optimised net EIP each year while preserving the base per-year sector / region
    shares.

    The split between gross-positive and removals depends on the removal
    ``strategy`` (read from the config):

    * ``"NEG"`` -- gross-positive emissions follow their own decay and are left
      unchanged; the removals absorb the optimised delta. The CDR components are
      rescaled so the total removals equal ``EIP_optimised - gross_positive``.
    * ``"POS"`` -- removals (CDR) are held constant; the gross-positive sectors
      absorb the optimised delta. The gross-positive sectors are rescaled so they
      equal ``EIP_optimised - removals``.

    In both cases the identity ``EIP = gross_positive + gross_removals`` holds and
    the rescaled World aggregate row is updated to match.

    Parameters
    ----------
    df_everything
        The (single-scenario) extensions dataframe returned by
        :func:`regionalize_fossil_co2`, with float year columns.
    strategy
        ``"NEG"`` or ``"POS"`` (case-insensitive).

    Returns
    -------
    pd.DataFrame
        ``df_everything`` with the fossil CO2 splits reconciled to the optimised
        net EIP.
    """
    strategy = str(strategy).upper()
    if strategy not in ("NEG", "POS"):
        raise ValueError(f"Unknown removal strategy {strategy!r}; expected 'NEG' or 'POS'.")

    df = df_everything.copy()
    year_cols = [c for c in df.columns if isinstance(c, (int, float))]

    var = df.index.get_level_values("variable")
    region = df.index.get_level_values("region")

    gp_mask = var.isin(GROSS_POSITIVE_SECTORS)
    cdr_mask = var.isin(CDR_COMPONENTS)
    eip_mask = (var == FOSSIL_VARIABLE) & (region == "World")
    pworld_mask = (var == GROSS_POSITIVE) & (region == "World")
    rworld_mask = (var == GROSS_REMOVALS) & (region == "World")

    if not eip_mask.any():
        raise ValueError(
            f"No World '{FOSSIL_VARIABLE}' row found; cannot rescale fossil splits."
        )

    eip_opt = df.loc[eip_mask, year_cols].iloc[0]
    pos_world = df.loc[pworld_mask, year_cols].iloc[0] if pworld_mask.any() else None
    rem_world = df.loc[rworld_mask, year_cols].iloc[0] if rworld_mask.any() else None

    if strategy == "NEG":
        if pos_world is None:
            raise ValueError("NEG strategy needs the World gross-positive row to derive removals.")
        rem_target = eip_opt - pos_world
        cdr_sum = df.loc[cdr_mask, year_cols].sum(axis=0)
        # Preserve per-year CDR-component shares; factor 1 where there is no CDR.
        factor = (rem_target / cdr_sum).where(cdr_sum != 0, 1.0).fillna(1.0)
        df.loc[cdr_mask, year_cols] = df.loc[cdr_mask, year_cols].mul(factor, axis=1)
        if rworld_mask.any():
            df.loc[rworld_mask, year_cols] = rem_target.values
    else:  # POS
        if rem_world is None:
            raise ValueError("POS strategy needs the World gross-removals row to derive gross positive.")
        pos_target = eip_opt - rem_world
        pos_sum = df.loc[gp_mask, year_cols].sum(axis=0)
        # Preserve per-year sector shares; factor 1 where there are no positive emissions.
        factor = (pos_target / pos_sum).where(pos_sum != 0, 1.0).fillna(1.0)
        df.loc[gp_mask, year_cols] = df.loc[gp_mask, year_cols].mul(factor, axis=1)
        if pworld_mask.any():
            df.loc[pworld_mask, year_cols] = pos_target.values

    return df


def load_regionalization_inputs(cfg: FlexConfig) -> dict:
    """Load the inputs required to regionalise fossil CO2 from the original CSVs.

    Replicates the data-loading section of 5191 (scenarios, history, regional
    data, regional fallback) and recomputes the 2100 split fractions, returning
    everything needed by :func:`regionalize_fossil_co2`.

    Non-CO2 (``df_all``) and CO2 AFOLU (``df_afolu``) are taken straight from the
    input file when ``read_non_co2_from_csv`` / ``read_afolu_from_csv`` are set
    (the counterfactual use-case). Recomputing those extensions is not supported
    here -- run 5191 for that path.
    """
    ds = cfg.data_sources or {}

    _global_paths = ds.get("scenarios_global", ["scenarios_complete_global.csv"])
    if isinstance(_global_paths, str):
        _global_paths = [_global_paths]
    _global_dfs = [pd.read_csv(DATA_DIR / p, index_col=[0, 1, 2, 3, 4, 5]) for p in _global_paths]
    scenarios_complete_global = pd.concat(_global_dfs) if len(_global_dfs) > 1 else _global_dfs[0]

    history = pd.read_csv(DATA_DIR / ds.get("history", "history.csv"), index_col=[0, 1, 2, 3, 4])

    _regional_path = ds.get("scenarios_regional", "scenarios_regional.csv")
    _regional_preview = pd.read_csv(DATA_DIR / _regional_path, nrows=0)
    _n_idx = sum(1 for c in _regional_preview.columns if not c.replace(".", "", 1).lstrip("-").isdigit())
    scenarios_regional = pd.read_csv(DATA_DIR / _regional_path, index_col=list(range(_n_idx)))

    # Numeric year columns; drop any that failed to parse.
    scenarios_complete_global.columns = pd.to_numeric(scenarios_complete_global.columns, errors="coerce")
    history.columns = pd.to_numeric(history.columns, errors="coerce")
    scenarios_regional.columns = pd.to_numeric(scenarios_regional.columns, errors="coerce")
    scenarios_complete_global = scenarios_complete_global.loc[:, scenarios_complete_global.columns.notna()]
    history = history.loc[:, history.columns.notna()]
    scenarios_regional = scenarios_regional.loc[:, scenarios_regional.columns.notna()]

    if "workflow" not in scenarios_regional.index.names:
        scenarios_regional["workflow"] = "for_scms"
        scenarios_regional = scenarios_regional.set_index("workflow", append=True)

    # Apply regional_scenario_fallback: duplicate regional/global data for missing scenarios.
    _fallback = ds.get("regional_scenario_fallback", {})
    if _fallback:
        _new_dfs = []
        _new_dfs_glob = []
        for target_scen, source_scen in _fallback.items():
            source = scenarios_regional.loc[pix.ismatch(scenario=source_scen)]
            if not source.empty:
                _new_dfs.append(source.rename(index={source_scen: target_scen}, level="scenario"))
            if target_scen not in scenarios_complete_global.pix.unique("scenario"):
                source_glob = scenarios_complete_global.loc[pix.ismatch(scenario=source_scen)]
                if not source_glob.empty:
                    _new_dfs_glob.append(source_glob.rename(index={source_scen: target_scen}, level="scenario"))
        if _new_dfs:
            scenarios_regional = pd.concat([scenarios_regional] + _new_dfs)
        if _new_dfs_glob:
            scenarios_complete_global = pd.concat([scenarios_complete_global] + _new_dfs_glob)

    scenarios_regional = scenarios_regional.sort_index(axis="columns").T.interpolate("index").T

    # Restrict to the model/scenario pairs used by this config.
    unique_model_scenario_pairs = scenarios_complete_global.index.droplevel(
        ["region", "variable", "unit", "workflow"]
    ).drop_duplicates()
    _config_pairs = {(v[1], v[0]) for v in cfg.scenario_model_match.values()}
    unique_model_scenario_pairs = unique_model_scenario_pairs[unique_model_scenario_pairs.isin(_config_pairs)]

    # Recompute the 2100 split fractions.
    fractions_fossil_total = {}
    for model, scen in unique_model_scenario_pairs.to_list():
        scen_here = scenarios_regional.loc[pix.ismatch(scenario=scen, model=model, variable="Emissions|CO2**")]
        _fractions_year = (
            cfg.scenario_end_year if cfg.scenario_end_year in scen_here.columns else scen_here.columns[-1]
        )
        fractions_list = get_2100_compound_composition_co2(scen_here[_fractions_year])
        fractions_fossil_total[(model, scen)] = {
            "fractions_tot_fossil": fractions_list[0],
            "fractions_cdr": fractions_list[1],
            "fractions_fossil_nocdr": fractions_list[2],
        }

    # Non-CO2 and AFOLU straight from the input file (counterfactual use-case).
    if not cfg.read_non_co2_from_csv:
        raise NotImplementedError(
            "load_regionalization_inputs only supports read_non_co2_from_csv=True. "
            "Run 5191 to compute non-CO2 extensions."
        )
    if not cfg.read_afolu_from_csv:
        raise NotImplementedError(
            "load_regionalization_inputs only supports read_afolu_from_csv=True. "
            "Run 5191 to compute AFOLU extensions."
        )
    df_all = scenarios_complete_global.loc[~pix.ismatch(variable="**CO2**")]
    df_afolu = scenarios_complete_global.loc[pix.ismatch(variable="**CO2|AFOLU**")]

    df_all = fix_year_columns_to_numeric(df_all)
    df_afolu = fix_year_columns_to_numeric(df_afolu)

    return {
        "scenarios_complete_global": scenarios_complete_global,
        "scenarios_regional": scenarios_regional,
        "history": history,
        "df_all": df_all,
        "df_afolu": df_afolu,
        "fractions_fossil_total": fractions_fossil_total,
    }


def build_global_fossil_extension_df(
    template_fossil: pd.DataFrame,
    co2_ffi_values: np.ndarray,
    fair_years: np.ndarray,
) -> pd.DataFrame:
    """Build a 5191-style global fossil extension dataframe from an optimised series.

    Parameters
    ----------
    template_fossil
        A single-row dataframe (or one selected via ``.iloc[[0]]``) of the source
        marker's fossil CO2 with index levels
        ``(model, scenario, region, variable, unit)`` and integer/float year
        columns. Used to copy the metadata/index and target year columns.
    co2_ffi_values
        Optimised fossil CO2 FFI values aligned with ``fair_years``.
    fair_years
        The (mid-year, e.g. 1750.5..2500.5) timepoints corresponding to
        ``co2_ffi_values``.

    Returns
    -------
    pd.DataFrame
        A one-row dataframe matching ``template_fossil``'s columns, with the
        optimised values resampled onto the template's year columns.
    """
    target_years = [c for c in template_fossil.columns if isinstance(c, int | float)]
    # Map each integer target year to the FaIR mid-year point (year + 0.5).
    interp = np.interp(
        np.asarray(target_years, dtype=float) + 0.5,
        np.asarray(fair_years, dtype=float),
        np.asarray(co2_ffi_values, dtype=float),
    )
    out = template_fossil.copy()
    out.loc[:, target_years] = interp
    return out


def write_extended_scenarios_csv(
    continuous_timeseries_concise: pd.DataFrame,
    outputs_dir: Path,
    scenario_model_match: dict,
    *,
    filename: str = "extended_scenarios_1750_2500.csv",
    continuous_filename: str = "continuous_emissions_timeseries_1750_2500.csv",
    fair_filename: str | None = "emissions_1750-2500.csv",
) -> Path:
    """Write the regionalised IAMC extended-scenarios CSV (+ optional FaIR CSV).

    Mirrors the final output cells of 5191: drops the internal gross-positive /
    gross-removals diagnostics, tags ``stage="extended"`` and drops the workflow
    level. When ``fair_filename`` is given, also writes the FaIR-format CSV.
    """
    outputs_dir = Path(outputs_dir)
    continuous_timeseries_extended = continuous_timeseries_concise.copy()

    internal_variables = [GROSS_POSITIVE, GROSS_REMOVALS]
    continuous_timeseries_extended = continuous_timeseries_extended.loc[
        ~continuous_timeseries_extended.index.get_level_values("variable").isin(internal_variables)
    ]
    continuous_timeseries_extended["stage"] = "extended"
    continuous_timeseries_extended = continuous_timeseries_extended.set_index("stage", append=True)
    continuous_timeseries_extended = continuous_timeseries_extended.droplevel("workflow")

    output_file = outputs_dir / filename
    continuous_timeseries_extended.to_csv(output_file)

    if fair_filename is not None:
        continuous_file = outputs_dir / continuous_filename
        continuous_timeseries_concise.to_csv(continuous_file)
        convert_continuous_to_fair_csv(
            str(continuous_file),
            str(outputs_dir / fair_filename),
            scenario_model_match,
        )

    return output_file
