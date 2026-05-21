# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Simple CO2 FFI Net-Zero Transition (no optimisation)
#
# Alternative to the `5195_optimise` + `5196_apply_optimised` workflow. For each
# marker listed in `cfg.optimization`, this notebook branches the source scenario's
# CO2 fossil-fuel emissions at a **departure year** and transitions them to net zero
# by a **net-zero year** using the same sigmoid / exponential algorithm that is
# applied to non-CO2 species in the main extension pipeline.  No FaIR simulation
# is required to determine the trajectory shape.
#
# **Config interpretation (reuses existing `optimization` block):**
#
# | parameter       | derived from                              |
# |-----------------|-------------------------------------------|
# | `departure_year`| first (lower) bound of `sig_start`        |
# | `net_zero_year` | last  (upper) bound of `sig_end`, capped at `extensions_end_year` |
#
# The transition algorithm (`do_simple_sigmoid_or_exponential_extension_to_target`)
# selects sigmoid or exponential decay based on the local derivative at the
# departure year, matching the non-CO2 extension behaviour.  With `sigmoid_shift=0`
# the transition starts immediately at `departure_year` and converges to zero at
# `net_zero_year`.  Sub-sectoral rows (if present) are extended independently and
# all target zero, preserving any regional / sectoral composition implicitly.
#
# **Outputs (augmented in-place):**
#
# 1. `emissions_1750-2500.csv` — FaIR-format CSV with CF scenario appended
# 2. `continuous_emissions_timeseries_1750_2500.csv` — IAMC full timeseries augmented
# 3. `extensions_full_emissions_timeseries_2023_2500.csv` — IAMC extensions augmented
# 4. `simple_trajectory_{marker}.png` — diagnostic CO2 FFI plot per marker
#
# Run **5191** before this notebook.  This notebook is a parallel alternative to
# running 5195 + 5196 and produces outputs in the same format.

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from flex.config import load_config, DATA_DIR
from flex.extension_functionality import (
    do_simple_sigmoid_or_exponential_extension_to_target,
    get_derivative_using_spline,
    get_sigmoid_derivative,
)
from flex.optimise import modify_emissions_csv, setup_fair

# %% tags=["parameters"]
config_name = "WIEMIP"
run_fair_verification = True

# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir

print(f"Config              : {cfg.name}")
print(f"All markers         : {list(cfg.scenario_model_match.keys())}")
print(f"Optimization markers: {list(cfg.optimization.keys())}")

# %% [markdown]
# ## Parse per-marker trajectory parameters from the optimization config block
#
# We reuse the `bounds` that the optimiser searches over to define the
# no-optimisation trajectory:
# - `departure_year` = lower bound of `sig_start`
# - `net_zero_year`  = upper bound of `sig_end`, capped at `extensions_end_year`

# %%
def _find_source_marker(marker: str, cfg) -> str:
    """Return the non-optimised marker that shares the same (scenario, model) pair."""
    base_scenario, base_model = cfg.scenario_model_match[marker][:2]
    for m, info in cfg.scenario_model_match.items():
        if m != marker and m not in cfg.optimization and info[0] == base_scenario and info[1] == base_model:
            return m
    raise ValueError(
        f"No non-optimised source marker found for '{marker}' "
        f"(scenario='{base_scenario}', model='{base_model}')"
    )


markers_to_process: dict[str, dict] = {}

for marker, opt_settings in cfg.optimization.items():
    if not opt_settings.get("enabled", True):
        print(f"Skipping {marker} (disabled in config)")
        continue

    departure_year = int(opt_settings["bounds"]["sig_start"][0])
    net_zero_year  = min(int(opt_settings["bounds"]["sig_end"][-1]), cfg.extensions_end_year)
    source_marker  = _find_source_marker(marker, cfg)

    markers_to_process[marker] = {
        "source_marker"  : source_marker,
        "source_scenario": cfg.scenario_model_match[source_marker][0],
        "source_model"   : cfg.scenario_model_match[source_marker][1],
        "departure_year" : departure_year,
        "net_zero_year"  : net_zero_year,
        "sigmoid_len"    : net_zero_year - departure_year,
    }

    print(f"\n{marker}:")
    print(f"  source         = {source_marker}  ({cfg.scenario_model_match[source_marker][0]})")
    print(f"  departure_year = {departure_year}")
    print(f"  net_zero_year  = {net_zero_year}  (capped: {net_zero_year < int(opt_settings['bounds']['sig_end'][-1])})")
    print(f"  sigmoid_len    = {net_zero_year - departure_year} years")

# %% [markdown]
# ## Locate input files (produced by 5191)

# %%
fair_csv       = OUTPUTS_DIR / "emissions_1750-2500.csv"
continuous_csv = OUTPUTS_DIR / "continuous_emissions_timeseries_1750_2500.csv"
extensions_csv = OUTPUTS_DIR / "extensions_full_emissions_timeseries_2023_2500.csv"

for path in [fair_csv, continuous_csv, extensions_csv]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file missing: {path}\n"
            "Run notebook 5191 first to generate extension outputs."
        )
    print(f"OK  {path.name}")

# %% [markdown]
# ## Load the IAMC continuous timeseries
#
# The continuous file (1750–2500) is used as the source for computing derivatives
# and the extension trajectory.  Using 1750-onwards data ensures the spline
# derivative estimator (which needs ~50 prior years) is always valid even for
# early departure years.

# %%
def _read_iamc_csv(path: Path) -> pd.DataFrame:
    """Read a CSV written from a MultiIndex DataFrame back into one."""
    df = pd.read_csv(path)
    year_cols = [c for c in df.columns if str(c).replace(".", "").replace("-", "").isdigit()]
    idx_cols  = [c for c in df.columns if c not in year_cols]
    df = df.set_index(idx_cols)
    df.columns = [float(c) for c in df.columns]
    return df


df_continuous = _read_iamc_csv(continuous_csv)
df_extensions = _read_iamc_csv(extensions_csv)

print(f"Continuous : {df_continuous.shape}  years {int(df_continuous.columns[0])}–{int(df_continuous.columns[-1])}")
print(f"Extensions : {df_extensions.shape}  years {int(df_extensions.columns[0])}–{int(df_extensions.columns[-1])}")
print(f"Index names: {df_continuous.index.names}")

# %% [markdown]
# ## Build simple CO2 FFI trajectories
#
# For each CF marker we:
# 1. Filter source-scenario rows from the continuous IAMC file for all
#    `Emissions|CO2|Energy and Industrial Processes` variables (total + sub-sectors).
# 2. For each row, truncate the timeseries at `departure_year` and apply
#    `do_simple_sigmoid_or_exponential_extension_to_target` with `target=0`.
# 3. Copy all other source rows (AFOLU, CH4, …) unchanged.
# 4. Store the resulting CF DataFrames for both the continuous and extensions files.

# %%
CO2_FFI_VAR = "Emissions|CO2|Energy and Industrial Processes"

scen_level = df_continuous.index.names.index("scenario")

# Integer year array spanning the full continuous timeseries (1750–2500)
t_vals = np.array(sorted(c for c in df_continuous.columns if isinstance(c, (int, float))))

iamc_cf_continuous: dict[str, pd.DataFrame] = {}
iamc_cf_extensions: dict[str, pd.DataFrame] = {}
transition_summary: dict[str, list[dict]] = {}

for marker, params in markers_to_process.items():
    src_scen   = params["source_scenario"]
    src_model  = params["source_model"]
    dep_yr     = params["departure_year"]
    nz_yr      = params["net_zero_year"]
    sig_len    = params["sigmoid_len"]
    t_extend   = int(dep_yr - t_vals[0])           # index of departure_year in t_vals

    print(f"\n{'='*60}")
    print(f"Building trajectory: {marker}  (departure {dep_yr} → net-zero {nz_yr})")
    print(f"{'='*60}")

    # --- filter source rows ---
    scen_mask  = df_continuous.index.get_level_values("scenario") == src_scen
    model_mask = df_continuous.index.get_level_values("model")    == src_model
    var_vals   = df_continuous.index.get_level_values("variable")
    co2_mask   = np.array(
        [v == CO2_FFI_VAR or v.startswith(f"{CO2_FFI_VAR}|") for v in var_vals]
    )
    source_co2   = df_continuous[scen_mask & model_mask &  co2_mask]
    source_other = df_continuous[scen_mask & model_mask & ~co2_mask]

    print(f"  CO2 FFI rows : {len(source_co2)}")
    print(f"  Other rows   : {len(source_other)}")

    if len(source_co2) == 0:
        print(f"  WARNING: no CO2 FFI rows found for source {params['source_marker']} — skipping")
        continue

    # --- extend each CO2 FFI row ---
    cf_co2_rows = []
    summary_rows = []

    for idx_tuple, row in source_co2.iterrows():
        values_all = row.values.astype(float)
        function   = values_all[: t_extend + 1]     # values up to and including departure_year

        # Determine transition type (matches the logic inside the extension function)
        deriv      = get_derivative_using_spline(function, t_vals, t_extend)
        sig_deriv  = get_sigmoid_derivative(0.0, function[-1], sigmoid_shift=0)
        t_type     = (
            "exponential"
            if (deriv < 0 and sig_deriv < 0 and abs(deriv) > abs(sig_deriv))
            else "sigmoid"
        )

        extended = do_simple_sigmoid_or_exponential_extension_to_target(
            function, t_vals, t_extend,
            target=0.0,
            sigmoid_shift=0,
            sigmoid_len=sig_len,
        )

        # Enforce hard net-zero: any residual after net_zero_year (e.g. from a
        # slow exponential tail that hasn't fully converged) is zeroed out.
        nz_idx = int(nz_yr - t_vals[0])
        extended[nz_idx:] = 0.0

        new_idx = list(idx_tuple)
        new_idx[scen_level] = marker
        cf_co2_rows.append(
            pd.Series(extended, index=t_vals, name=tuple(new_idx))
        )

        var_short = idx_tuple[df_continuous.index.names.index("variable")].split("|")[-1]
        region    = idx_tuple[df_continuous.index.names.index("region")]
        print(f"    [{t_type:11s}]  {var_short[:45]:45s}  region={region}")
        summary_rows.append({"variable": var_short, "region": region, "transition": t_type})

    transition_summary[marker] = summary_rows

    # --- copy other rows unchanged ---
    cf_other_rows = []
    for idx_tuple, row in source_other.iterrows():
        new_idx = list(idx_tuple)
        new_idx[scen_level] = marker
        cf_other_rows.append(row.rename(tuple(new_idx)))

    # --- assemble CF DataFrames ---
    all_rows = cf_co2_rows + cf_other_rows
    idx_mi   = pd.MultiIndex.from_tuples(
        [r.name for r in all_rows], names=df_continuous.index.names
    )
    df_cf = pd.DataFrame(
        [r.values for r in all_rows],
        index=idx_mi,
        columns=t_vals,
    )

    iamc_cf_continuous[marker] = df_cf

    ext_cols = [c for c in t_vals if c >= df_extensions.columns[0]]
    iamc_cf_extensions[marker] = df_cf[ext_cols]

print(f"\nBuilt CF blocks for: {list(iamc_cf_continuous.keys())}")

# %% [markdown]
# ## Augment and save IAMC files
#
# Append the CF scenario rows to both the continuous (1750–2500) and
# extensions-only (2023–2500) IAMC CSV files, overwriting them in place.

# %%
# --- continuous ---
df_cont_aug = pd.concat([df_continuous] + list(iamc_cf_continuous.values()))
df_cont_aug.columns = [str(int(c)) for c in df_cont_aug.columns]
df_cont_aug.to_csv(continuous_csv)
print(f"Updated  continuous CSV : {continuous_csv.name}  ({len(df_cont_aug)} rows)")

# --- extensions ---
df_ext_aug = pd.concat([df_extensions] + list(iamc_cf_extensions.values()))
df_ext_aug.columns = [str(int(c)) for c in df_ext_aug.columns]
df_ext_aug.to_csv(extensions_csv)
print(f"Updated  extensions CSV : {extensions_csv.name}  ({len(df_ext_aug)} rows)")

# %% [markdown]
# ## Augment FaIR-format emissions CSV
#
# For each CF marker extract the World-total CO2 FFI trajectory from the IAMC
# CF block, interpolate it onto FaIR's mid-year grid, then call
# `modify_emissions_csv` (same as 5196) to append the CF scenario.

# %%
current_csv = str(fair_csv)

for marker, params in markers_to_process.items():
    if marker not in iamc_cf_continuous:
        print(f"Skipping {marker} (no CF block built)")
        continue

    source_marker = params["source_marker"]
    dep_yr        = params["departure_year"]

    # Extract World-total CO2 FFI from the CF IAMC block
    df_cf   = iamc_cf_continuous[marker]
    region_vals = df_cf.index.get_level_values("region")
    var_vals    = df_cf.index.get_level_values("variable")

    world_total = df_cf[
        (region_vals == "World") & (var_vals == CO2_FFI_VAR)
    ]

    if len(world_total) == 0:
        # No explicit World total — sum sub-sectors at World level
        world_subs = df_cf[(region_vals == "World") & (var_vals != CO2_FFI_VAR)]
        if len(world_subs) == 0:
            raise ValueError(f"Cannot find World CO2 FFI (total or sub-sectors) for {marker}")
        world_values = world_subs.sum(axis=0).values
    else:
        world_values = world_total.iloc[0].values   # (751,) over integer years 1750–2500

    # Read FaIR CSV to get its mid-year grid
    df_fair     = pd.read_csv(current_csv)
    year_cols_f = [c for c in df_fair.columns if c.replace(".", "").replace("-", "").isdigit()]
    years_fair  = np.array([float(c) for c in year_cols_f])  # e.g. 1750.5, 1751.5, …

    # Interpolate: IAMC integer years ↔ FaIR mid-year floats (year X ≙ X+0.5 in FaIR)
    co2_ffi_fair = np.interp(years_fair - 0.5, t_vals, world_values)

    # Write augmented FaIR CSV
    out_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
    modify_emissions_csv(
        current_csv,
        source_marker,
        marker,
        co2_ffi_trajectory=co2_ffi_fair,
        departure_year=dep_yr,
        output_path=out_csv,
    )
    current_csv = out_csv
    print(f"Applied {marker}  (source={source_marker}, departure={dep_yr})")

df_check = pd.read_csv(current_csv, usecols=["scenario"]).drop_duplicates()
print(f"\nScenarios in FaIR CSV: {sorted(df_check['scenario'].unique())}")

# %% [markdown]
# ## Diagnostic plots
#
# CO2 FFI for source vs. CF marker, with vertical lines at departure and
# net-zero years.

# %%
df_fair_final = pd.read_csv(current_csv)
year_cols_f   = [c for c in df_fair_final.columns if c.replace(".", "").replace("-", "").isdigit()]
years_fair    = np.array([float(c) for c in year_cols_f])

for marker, params in markers_to_process.items():
    if marker not in iamc_cf_continuous:
        continue

    source_marker = params["source_marker"]
    dep_yr        = params["departure_year"]
    nz_yr         = params["net_zero_year"]
    source_color  = cfg.scenario_model_match[source_marker][2]
    marker_color  = cfg.scenario_model_match[marker][2]

    fig, ax = plt.subplots(figsize=(12, 5))

    src_row = df_fair_final[
        (df_fair_final["scenario"] == source_marker) & (df_fair_final["variable"] == "CO2 FFI")
    ]
    cf_row = df_fair_final[
        (df_fair_final["scenario"] == marker) & (df_fair_final["variable"] == "CO2 FFI")
    ]

    if len(src_row):
        ax.plot(years_fair, src_row[year_cols_f].values.flatten(),
                label=source_marker, color=source_color, linewidth=2)
    if len(cf_row):
        ax.plot(years_fair, cf_row[year_cols_f].values.flatten(),
                label=marker, color=marker_color, linewidth=2, linestyle="--")

    ax.axvline(dep_yr, color="gray",  linestyle=":",  linewidth=1.5, label=f"Departure ({dep_yr})")
    ax.axvline(nz_yr,  color="black", linestyle=":",  linewidth=1.0, alpha=0.6,
               label=f"Net-zero target ({nz_yr})")
    ax.axhline(0,      color="black", linewidth=0.5,  alpha=0.4)

    ax.set_xlim(1900, cfg.extensions_end_year)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 FFI (Mt CO2/yr)")
    ax.set_title(f"{marker}: simple net-zero trajectory  [departure {dep_yr} → net-zero {nz_yr}]")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    out_png = OUTPUTS_DIR / f"simple_trajectory_{marker}.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out_png.name}")

# %% [markdown]
# ## Summary

# %%
print(f"\n{'='*90}")
print("SIMPLE TRAJECTORY SUMMARY")
print(f"{'='*90}")

summary_rows = []
for marker, params in markers_to_process.items():
    if marker not in iamc_cf_continuous:
        continue

    cf_row = df_fair_final[
        (df_fair_final["scenario"] == marker) & (df_fair_final["variable"] == "CO2 FFI")
    ]
    if len(cf_row):
        ffi_vals  = cf_row[year_cols_f].values.flatten()
        dep_idx   = int(np.searchsorted(years_fair, params["departure_year"] + 0.5))
        ffi_at_dep = ffi_vals[dep_idx]
        ffi_at_end = ffi_vals[-1]
    else:
        ffi_at_dep = ffi_at_end = float("nan")

    # Consolidate transition types for this marker
    ttypes = {r["transition"] for r in transition_summary.get(marker, [])}
    t_label = "/".join(sorted(ttypes)) if ttypes else "n/a"

    summary_rows.append({
        "Marker"        : marker,
        "Source"        : params["source_marker"],
        "Departure yr"  : params["departure_year"],
        "Net-zero yr"   : params["net_zero_year"],
        "Sigmoid len"   : params["sigmoid_len"],
        "FFI@departure" : f"{ffi_at_dep:.0f}",
        "FFI@end"       : f"{ffi_at_end:.2f}",
        "Transition"    : t_label,
    })

df_summary = pd.DataFrame(summary_rows)
print(df_summary.to_string(index=False))
print(f"{'='*90}")
print("\nNext step: Run 5201 to simulate FaIR with all scenarios including these CF trajectories")

# %% [markdown]
# ## Optional: FaIR temperature verification
#
# Set `run_fair_verification = True` (parameters cell) to check whether
# the simple trajectory produces a plausible temperature response.
# This uses a small 5-member ensemble so runs quickly.

# %%
if run_fair_verification:
    print("Running FaIR verification ...")
    all_scenarios = sorted(
        pd.read_csv(current_csv, usecols=["scenario"])["scenario"].unique()
    )
    _conc_file = (
        str(DATA_DIR / cfg.concentrations_file)
        if cfg.concentrations_file is not None
        else None
    )
    f = setup_fair(
        current_csv,
        all_scenarios,
        memory_limited=True,
        scenario_mapping={**cfg.scenario_mapping, **cfg.forcing_scenario},
        concentrations_file=_conc_file,
    )
    f.run()
    timebounds = f.timebounds
    print("FaIR run complete")

    for marker, params in markers_to_process.items():
        if marker not in iamc_cf_continuous:
            continue
        source_marker = params["source_marker"]
        dep_yr        = params["departure_year"]
        source_color  = cfg.scenario_model_match[source_marker][2]
        marker_color  = cfg.scenario_model_match[marker][2]

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        # Temperature
        ax = axes[0]
        src_t = f.temperature.sel(scenario=source_marker, layer=0).median(dim="config").values
        cf_t  = f.temperature.sel(scenario=marker,        layer=0).median(dim="config").values
        ax.plot(timebounds, src_t, label=source_marker, color=source_color, linewidth=2)
        ax.plot(timebounds, cf_t,  label=marker,        color=marker_color, linewidth=2, linestyle="--")
        ax.axvline(dep_yr, color="gray",  linestyle=":", linewidth=1,   label=f"Departure ({dep_yr})")
        ax.axvline(nz_yr,  color="black", linestyle=":", linewidth=0.8, alpha=0.6,
                   label=f"Net-zero ({nz_yr})")
        ax.set_xlim(1900, 2500)
        ax.set_xlabel("Year")
        ax.set_ylabel("Temperature anomaly (K)")
        ax.set_title(f"{marker} vs {source_marker}: Temperature")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # CO2 FFI emissions
        ax = axes[1]
        src_ffi_row = df_fair_final[
            (df_fair_final["scenario"] == source_marker) & (df_fair_final["variable"] == "CO2 FFI")
        ]
        cf_ffi_row = df_fair_final[
            (df_fair_final["scenario"] == marker) & (df_fair_final["variable"] == "CO2 FFI")
        ]
        if len(src_ffi_row):
            ax.plot(years_fair, src_ffi_row[year_cols_f].values.flatten(),
                    label=source_marker, color=source_color, linewidth=2)
        if len(cf_ffi_row):
            ax.plot(years_fair, cf_ffi_row[year_cols_f].values.flatten(),
                    label=marker, color=marker_color, linewidth=2, linestyle="--")
        ax.axvline(dep_yr, color="gray",  linestyle=":", linewidth=1)
        ax.axvline(nz_yr,  color="black", linestyle=":", linewidth=0.8, alpha=0.6)
        ax.axhline(0, color="black", linewidth=0.5, alpha=0.4)
        ax.set_xlim(1900, 2500)
        ax.set_xlabel("Year")
        ax.set_ylabel("CO2 FFI (Mt CO2/yr)")
        ax.set_title(f"{marker} vs {source_marker}: CO2 FFI")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Cumulative CO2 FFI
        ax = axes[2]
        src_cum = f.cumulative_emissions.sel(scenario=source_marker, specie="CO2 FFI").mean(dim="config").values
        cf_cum  = f.cumulative_emissions.sel(scenario=marker,        specie="CO2 FFI").mean(dim="config").values
        ax.plot(timebounds, src_cum, label=source_marker, color=source_color, linewidth=2)
        ax.plot(timebounds, cf_cum,  label=marker,        color=marker_color, linewidth=2, linestyle="--")
        ax.axvline(dep_yr, color="gray",  linestyle=":", linewidth=1)
        ax.axvline(nz_yr,  color="black", linestyle=":", linewidth=0.8, alpha=0.6)
        ax.set_xlim(1900, 2500)
        ax.set_xlabel("Year")
        ax.set_ylabel("Cumulative CO2 FFI (GtCO2)")
        ax.set_title(f"{marker} vs {source_marker}: Cumulative CO2 FFI")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        out_png = OUTPUTS_DIR / f"simple_trajectory_{marker}_fair_verification.png"
        plt.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"Saved: {out_png.name}")
else:
    print("FaIR verification skipped.  Set run_fair_verification=True to enable.")
