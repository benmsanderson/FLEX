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

# %%
# ruff: noqa: E402

# %% [markdown]
# # Extensions of Marker Scenarios

# %% [markdown]
# Regular imports

# %%
import glob
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import openscm_units
import pandas as pd
import pandas_indexing as pix
import pandas_openscm
import seaborn as sns
import tqdm.auto

from flex.config import load_config, DATA_DIR
from flex.afolu_extension_functions import (
    get_cumulative_afolu,
    extend_one_scenario_afolu,
)
from flex.cdr_and_fossil_splits import (
    add_removals_and_positive_fossil_emissions_to_historical,
    extend_cdr_components_vectorized,
    get_2100_compound_composition_co2,
)

from flex.extension_functionality import (
    sigmoid_function,
)
from flex.extensions_functions_for_non_co2 import (
    do_single_component_for_scenario_model_regionally,
)
from flex.finish_regional_extensions import (
    extend_regional_for_missing,
    merge_historical_future_timeseries,
)
from flex.regionalize_fossil import regionalize_fossil_co2
from flex.fossil_co2_storyline_functions import (
    process_single_scenario_storyline_wrapper,
)
from flex.general_utils_for_extensions import (
    fix_up_and_concatenate_extensions,
    interpolate_to_annual,
    fix_year_columns_to_numeric,
    save_continuous_timeseries_to_csv,
)

# %% tags=["parameters"]
config_name = "vl-frankenstein"  # Name of the config file (without .yaml) in configs/ to use for this notebook
#config_name = "scenariomip_default"

# --- Load ensemble configuration ---
# %%
cfg = load_config(config_name)
print(cfg)
OUTPUTS_DIR = cfg.outputs_dir
print(f"Loaded config: {cfg.name}")
print(f"Outputs: {OUTPUTS_DIR}")
print(f"Plots: {cfg.plots_dir}")

# Constants (from config)
FUTURE_START_YEAR = cfg.future_start_year
HISTORICAL_START_YEAR = cfg.historical_start_year
SCENARIO_END_YEAR = cfg.scenario_end_year
EXTENSIONS_END_YEAR = cfg.extensions_end_year
TUPLE_LENGTH_WITH_STAGE = 6

# %% tags=["parameters"]
# Papermill parameters
make_plots: bool = cfg.make_plots
dump_csvs: bool = cfg.dump_csvs
read_non_co2_from_csv: bool = cfg.read_non_co2_from_csv
read_afolu_from_csv: bool = cfg.read_afolu_from_csv

# %% [markdown]
# ## Loading scenarios

# %%
# Load data from CSV files — uses cfg.data_sources if set, otherwise standard defaults
ds = cfg.data_sources or {}
print(ds)
print(cfg)


# scenarios_global: list of files to concatenate, or single default
_global_paths = ds.get("scenarios_global", ["scenarios_complete_global.csv"])
if isinstance(_global_paths, str):
    _global_paths = [_global_paths]
print(_global_paths)


print("Loading scenarios_complete_global from CSV...")
_global_dfs = [pd.read_csv(DATA_DIR / p, index_col=[0, 1, 2, 3, 4, 5]) for p in _global_paths]
scenarios_complete_global = pd.concat(_global_dfs) if len(_global_dfs) > 1 else _global_dfs[0]
print(f"Loaded scenarios_complete_global: {scenarios_complete_global.shape}")

print(scenarios_complete_global.index.names)
print(scenarios_complete_global.head())
print("Loading history from CSV...")
history = pd.read_csv(
    DATA_DIR / ds.get("history", "history.csv"),
    index_col=[0, 1, 2, 3, 4]
)
print(f"Loaded history: {history.shape}")

# scenarios_regional: may have 5 or 6-level index depending on data source
_regional_path = ds.get("scenarios_regional", "scenarios_regional.csv")
print("Loading scenarios_regional from CSV...")
# Detect index width by counting non-numeric leading columns
_regional_preview = pd.read_csv(DATA_DIR / _regional_path, nrows=0)
_n_idx = sum(1 for c in _regional_preview.columns if not c.replace('.', '', 1).lstrip('-').isdigit())
scenarios_regional = pd.read_csv(DATA_DIR / _regional_path, index_col=list(range(_n_idx)))
print(f"Loaded scenarios_regional: {scenarios_regional.shape}")

print("Loading history_regional from CSV...")
history_regional = pd.read_csv(
    DATA_DIR / ds.get("history_regional", "history_regional.csv"),
    index_col=[0, 1, 2, 3, 4, 5]
)


print(f"Loaded history_regional: {history_regional.shape}")

# Convert year columns to numeric types
print("\nConverting column names to numeric types...")
scenarios_complete_global.columns = pd.to_numeric(scenarios_complete_global.columns, errors='coerce')
history.columns = pd.to_numeric(history.columns, errors='coerce')
scenarios_regional.columns = pd.to_numeric(scenarios_regional.columns, errors='coerce')
history_regional.columns = pd.to_numeric(history_regional.columns, errors='coerce')

# Drop any NaN columns that may have been created
print("\nDropping any NaN columns...")
scenarios_complete_global = scenarios_complete_global.loc[:, scenarios_complete_global.columns.notna()]
history = history.loc[:, history.columns.notna()]
scenarios_regional = scenarios_regional.loc[:, scenarios_regional.columns.notna()]
history_regional = history_regional.loc[:, history_regional.columns.notna()]


# Add 'workflow' level to scenarios_regional if missing
if 'workflow' not in scenarios_regional.index.names:
    print("\nAdding 'workflow' level to scenarios_regional...")
    scenarios_regional['workflow'] = 'for_scms'
    scenarios_regional = scenarios_regional.set_index('workflow', append=True)
    print(f"  scenarios_regional now has index: {scenarios_regional.index.names}")

print(f"  scenarios_complete_global columns dtype: {scenarios_complete_global.columns.dtype}")
print(f"  history columns dtype: {history.columns.dtype}")
print(f"  scenarios_regional columns dtype: {scenarios_regional.columns.dtype}")
print(f"  history_regional columns dtype: {history_regional.columns.dtype}")

# %%
unique_model_scenario_pairs = scenarios_complete_global.index.droplevel(
    ["region", "variable", "unit", "workflow"]
).drop_duplicates()

# Filter to only model/scenario pairs used by this config's markers
print(unique_model_scenario_pairs)
_config_pairs = {(v[1], v[0]) for v in cfg.scenario_model_match.values()}
unique_model_scenario_pairs = unique_model_scenario_pairs[
    unique_model_scenario_pairs.isin(_config_pairs)
]

print(f"Number of unique model-scenario pairs: {len(unique_model_scenario_pairs)}")
print("\nUnique model-scenario pairs:")
for i, (model, scenario) in enumerate(unique_model_scenario_pairs, 1):
    print(f"{i:2d}. {model} | {scenario}")


# Apply regional_scenario_fallback: duplicate regional data for missing scenarios
_fallback = ds.get("regional_scenario_fallback", {})
if _fallback:
    _new_dfs = []
    _new_dfs_glob = []
    for target_scen, source_scen in _fallback.items():
        source = scenarios_regional.loc[pix.ismatch(scenario=source_scen)]
        if not source.empty:
            new = source.rename(index={source_scen: target_scen}, level="scenario")
            _new_dfs.append(new)
            print(f"  Fallback: copied regional data from '{source_scen}' -> '{target_scen}'")
        if target_scen not in scenarios_complete_global.pix.unique("scenario"):
            source_glob = scenarios_complete_global.loc[pix.ismatch(scenario=source_scen)]
            if not source_glob.empty:
                new_glob = source_glob.rename(index={source_scen: target_scen}, level="scenario")
                _new_dfs_glob.append(new_glob)
                print(f"  Fallback: copied global data from '{source_scen}' -> '{target_scen}'")

    if _new_dfs:
        scenarios_regional = pd.concat([scenarios_regional] + _new_dfs)
    if _new_dfs_glob:
        scenarios_complete_global = pd.concat([scenarios_complete_global] + _new_dfs_glob)
        print(f"Hello")
print(scenarios_regional.pix.unique("scenario"))
print(scenarios_complete_global.pix.unique("scenario"))
#sys.exit(4)

# %%
unique_model_scenario_pairs = scenarios_complete_global.index.droplevel(
    ["region", "variable", "unit", "workflow"]
).drop_duplicates()

# Filter to only model/scenario pairs used by this config's markers
print(unique_model_scenario_pairs)
_config_pairs = {(v[1], v[0]) for v in cfg.scenario_model_match.values()}
unique_model_scenario_pairs = unique_model_scenario_pairs[
    unique_model_scenario_pairs.isin(_config_pairs)
]
print(_config_pairs)
print(f"Number of unique model-scenario pairs: {len(unique_model_scenario_pairs)}")
print("\nUnique model-scenario pairs:")
for i, (model, scenario) in enumerate(unique_model_scenario_pairs, 1):
    print(f"{i:2d}. {model} | {scenario}")

#sys.exit(4)
# %% [markdown]
# Marker definitions

# %%
scenario_model_match = {
    k: v for k, v in cfg.scenario_model_match.items()
    if k not in cfg.optimization
}
print(f"Processing {len(scenario_model_match)} markers (excluding optimized: {list(cfg.optimization.keys())})")

# %%
scenarios_regional = scenarios_regional.sort_index(axis="columns").T.interpolate("index").T

fractions_fossil_total = {}
for model, scen in unique_model_scenario_pairs.to_list():
    print(f"Processing {model} | {scen}")
    tot_co2 = scenarios_complete_global.loc[pix.ismatch(scenario=scen, model=model, variable="Emissions|CO2")]
    scen_here = scenarios_regional.loc[pix.ismatch(scenario=scen, model=model, variable="Emissions|CO2**")]
    # Use SCENARIO_END_YEAR if available, otherwise fall back to last available year
    _fractions_year = SCENARIO_END_YEAR if SCENARIO_END_YEAR in scen_here.columns else scen_here.columns[-1]
    fractions_list = get_2100_compound_composition_co2(scen_here[_fractions_year])
    fractions_fossil_total[(model, scen)] = {
        "fractions_tot_fossil": fractions_list[0],
        "fractions_cdr": fractions_list[1],
        "fractions_fossil_nocdr": fractions_list[2],
    }

# %% [markdown]
# Finally get cumulative CO2 history

# %%
cumulative_history_afolu = get_cumulative_afolu(history, "GCB-extended", "historical")

# %% [markdown]
# ## Main block for AFOLU


# %%
# AFOLU section
def calculate_afolu_extensions(scenarios_complete_global, history, cumulative_history_afolu, plot=True):
    """
    Calculate AFOLU extensions for all scenarios and models
    """
    temp_list_for_new_data_linear_ramp_down = []
    for s, meta in scenario_model_match.items():
        df_afolu_linear_ramp_down = extend_one_scenario_afolu(
            scenarios_complete_global, history, cumulative_history_afolu, meta[1], meta[0],
            extension_end_year=EXTENSIONS_END_YEAR,
        )

        temp_list_for_new_data_linear_ramp_down.append(df_afolu_linear_ramp_down)
    extended_data_afolu_linear_ramp_down = pd.concat(temp_list_for_new_data_linear_ramp_down)
    return {
        "linear_afolu_rampdown": extended_data_afolu_linear_ramp_down,
    }


# %% [markdown]
# ## Non-CO2 functionality

# %% [markdown]
# First defining some non-zero end-points for certain gases per marker:

# %%
component_global_targets = cfg.component_global_targets

# %% [markdown]
# Main functionality for all non-co2 extensions


# %%
# Diagnostic: Check scenarios_regional index structure
print("=== SCENARIOS_REGIONAL INDEX STRUCTURE ===")
print(f"Index names: {scenarios_regional.index.names}")
print(f"Index levels: {scenarios_regional.index.nlevels}")
print(f"Sample index values:")
print(scenarios_regional.index[:5])

# %%
def do_all_non_co2_extensions(scenarios_complete_global, history):  # noqa: PLR0912
    """
    Extend all non-CO2 emission variables across scenarios and models using historical data and global targets.

    Iterates over all emission variables (excluding CO2) in the provided global scenarios dataset, matches them with
    scenario-model pairs, and applies regional extension logic. For each variable and scenario-model pair, it computes
    the extended data using historical values and optional global targets, then aggregates the results.
    Optionally, generates diagnostic plots for each variable and scenario-model pair.

    Parameters
    ----------
    scenarios_complete_global : pyam.IamDataFrame
        Complete global scenarios dataset containing emission variables.
    history : pyam.IamDataFrame
        Historical emissions data for matching and extension.

    Returns
    -------
    pd.DataFrame
        Concatenated DataFrame of all extended non-CO2 emission variables across scenarios and models.
    """
    total_df_list = []

    for variable in tqdm.auto.tqdm(scenarios_complete_global.pix.unique("variable").values):
        print(variable)
        # print(history.loc[pix.ismatch(variable=f"{variable}")].shape)
        if variable.startswith("Emissions|CO2"):
            continue
        if history.loc[pix.ismatch(variable=f"{variable}")].shape[0] < 1:
            continue
        for s, meta in tqdm.auto.tqdm(scenario_model_match.items()):
            # Parse the normalized non_co2_targets entry.
            # If the variable is configured and this scenario is NOT listed,
            # skip it (keep source data).  If the variable is not configured
            # at all, every scenario gets the default auto-decay extension.
            var_targets = component_global_targets.get(variable)
            if var_targets is not None and s not in var_targets:
                print(f"{s}: {meta}, SKIP (not configured for {variable})")
                continue
            if var_targets is not None:
                target_entry = var_targets[s]
                global_target = target_entry.get("target")
                sig_shift = target_entry.get("sigmoid_shift", 40)
                sig_len = target_entry.get("sigmoid_len", 50)
                branch_year = target_entry.get("branch_year", int(SCENARIO_END_YEAR))
            else:
                global_target = None
                sig_shift = 40
                sig_len = 50
                branch_year = int(SCENARIO_END_YEAR)
            print(f"{s}: {meta}, target: {global_target}, branch: {branch_year}")
            df_comp_scen_model = do_single_component_for_scenario_model_regionally(
                meta[0],
                meta[1],
                variable,
                scenarios_regional,
                scenarios_complete_global,
                history,
                global_target=global_target,
                end_year=EXTENSIONS_END_YEAR,
                end_scenario_year=branch_year,
                sigmoid_shift=sig_shift,
                sigmoid_len=sig_len,
            )
            # if "workflow" in df_comp_scen_model.index.names:
            #     print("Dropping workflow level from index")
            #     df_comp_scen_model = df_comp_scen_model.droplevel(["workflow"])
            # # sys.exit(4)
            if "workflow" not in df_comp_scen_model.index.names:
                print(f"Workflow missing for {s}: {meta}, {variable}, adding level")
                print(df_comp_scen_model)
                sys.exit(4)
            total_df_list.append(df_comp_scen_model)
            # print(df_comp_scen_model.columns)
    df_all = pix.concat(total_df_list)
    return df_all


# %% [markdown]
# ## Do main block of non-fossil CO2 extensions first

# %%
# Set this to true if running for the first time to generate CSVs
# Otherwise you can set to false to speed-up by not running throuhg
# all the non-CO2 and afolu extensions again
do_and_write_to_csv = False
if read_non_co2_from_csv:
    print("Reading non-CO2 extensions from CSV...")
    do_and_write_to_csv = False
    df_all = scenarios_complete_global.loc[~pix.ismatch(variable="**CO2**")]
elif do_and_write_to_csv:
    df_all = do_all_non_co2_extensions(scenarios_complete_global, history)

else:
    print("Reading non-CO2 extensions from CSV in folder...")
    df_all = pd.read_csv("first_draft_extended_nonCO2_all.csv", index_col=[0, 1, 2, 3, 4, 5])
#sys.exit(4)         

if read_afolu_from_csv:
    do_and_write_to_csv = False
    afolu_dfs = {}
    afolu_dfs["linear_afolu_rampdown"] = scenarios_complete_global.loc[pix.ismatch(variable="**CO2|AFOLU**")]
    # df_compare = pd.read_csv("first_draft_extended_afolu_linear_afolu_rampdown.csv", index_col=[0, 1, 2, 3, 4])
    #print(afolu_dfs["linear_afolu_rampdown"].shape, df_compare.shape)
    #print(afolu_dfs["linear_afolu_rampdown"].head(), df_compare.head())
elif do_and_write_to_csv:
    afolu_dfs = calculate_afolu_extensions(
        scenarios_complete_global, history, cumulative_history_afolu, plot=make_plots
    )
    if dump_csvs:
        df_all.to_csv(OUTPUTS_DIR / "first_draft_extended_nonCO2_all.csv")
        for name, afolu_df in afolu_dfs.items():
            afolu_df.to_csv(OUTPUTS_DIR / f"first_draft_extended_afolu_{name}.csv")
else:
    afolu_dfs = {}
    for afolu_file in glob.glob("first_draft_extended_afolu_linear*.csv"):
        print("Reading " + afolu_file)
        name = afolu_file.split("first_draft_extended_afolu_")[-1].split(".csv")[0]

        afolu_dfs[name] = pd.read_csv(afolu_file, index_col=[0, 1, 2, 3, 4])
#sys.exit(4)
# %% [markdown]
# # Total CO2 Storyline dictionaries
# These dictionaries define how total CO2 emissions evolve from 2023 to 2500
# Each storyline type has specific parameters that control the transition phases
# ## Storyline Types (from extensions_fossil_co2_storyline_functions.py):
# - "CS": Constant-then-Sigmoid - holds constant emissions, then smooth transition to zero
# - "ECS": Exponential/linear-then-Constant-then-Sigmoid - initial decay/growth, plateau, then transition to zero
# - "CSCS": Constant-Sigmoid-Constant-Sigmoid - two-phase transition with intermediate plateau
# ## Parameter meanings:
# ### CS storyline: ["CS", stop_const, end_sig, roll_in, roll_out]
# - stop_const: year when constant phase ends
# - end_sig: year when sigmoid transition to zero completes
# - roll_in: years for smooth roll-in to sigmoid (transition smoothing)
# - roll_out: years for smooth roll-out from sigmoid (transition smoothing)
# ### ECS storyline: ["ECS", exp_end, exp_targ, sig_start, sig_end, roll_in, roll_out]
# - exp_end: year when initial exponential/linear phase ends
# - exp_targ: target emission value at exp_end (None = auto-calculated from data trend)
# - sig_start: year when sigmoid transition begins
# - sig_end: year when sigmoid transition to zero completes
# - roll_in, roll_out: transition smoothing parameters (years)
# ### CSCS storyline: ["CSCS", stop_const, sig_targ, end_sig1, start_sig2, end_sig2, roll_in, roll_out]
# - stop_const: year when first constant phase ends
# - sig_targ: target value for intermediate plateau (between two sigmoids)
# - end_sig1: year when first sigmoid completes
# - start_sig2: year when second sigmoid begins
# - end_sig2: year when final sigmoid to zero completes
# - roll_in, roll_out: transition smoothing parameters (years)

# %%
# ["CS",stop_const,end_sig,roll_in,roll_out]
# ["ECS",exp_end,exp_targ,sig_start,sig_end,roll_in,roll_out]
# ["CSCS",stop_const,sig_targ,end_sig1,start_sig2,end_sig2,roll_in,roll_out]

fossil_evolution_dictionary = cfg.fossil_evolution_dictionary


# %% [markdown]
# Looping over afolu variants to get CO2

# %%
name = "linear_afolu_rampdown"
df_afolu = afolu_dfs[name]
temp_list_for_new_data = []
for s, meta in scenario_model_match.items():
    print(f"Processing fossil CO2 to match storyline and AFOLU for {s}")
    if meta[0] in df_afolu.pix.unique("scenario"):
        # Standard case:
        co2_fossil = interpolate_to_annual(
            scenarios_complete_global.loc[
                pix.ismatch(
                    variable="Emissions|CO2|Energy and Industrial Processes",
                    model=meta[1],
                    scenario=meta[0],
                    workflow="for_scms",
                )
            ]
        )
    else:
        # Hard overwrite to make Frankenstein work:
        co2_fossil = interpolate_to_annual(
            scenarios_complete_global.loc[
                pix.ismatch(
                    variable="Emissions|CO2|Energy and Industrial Processes",
                    model=meta[1],
                    workflow="for_scms",
                )
            ]
        )       

    # co2_afolu = df_afolu.loc[(df_afolu["model"] == meta[1]) & (df_afolu["scenario"] == meta[0])]
    co2_afolu = df_afolu.loc[pix.ismatch(model=meta[1], scenario=meta[0])]
    print(df_afolu.pix.unique("model"))
    print(df_afolu.pix.unique("scenario"))
    print("meta: ", meta)
    if meta[0] not in df_afolu.pix.unique("scenario"):
        # Hard overwrite to make Frankenstein work:
        co2_afolu = df_afolu.loc[pix.ismatch(model=meta[1])]
    if co2_afolu.shape[0] > 1:
        print("Hello")
        co2_afolu = co2_afolu.iloc[0:1]  # Take the first row if multiple exist

    print(co2_fossil.shape, co2_afolu.shape)
    #sys.exit(4)
    df_total = process_single_scenario_storyline_wrapper(
        co2_fossil, 
        co2_afolu, 
        fossil_evolution_dictionary[s],
        start = int(FUTURE_START_YEAR),
        end = EXTENSIONS_END_YEAR,
        scenario_end = int(SCENARIO_END_YEAR),
        history_start = HISTORICAL_START_YEAR,
        )
    temp_list_for_new_data.append(df_total)

fossil_extension_df = pd.concat(temp_list_for_new_data)
if dump_csvs:
    fossil_extension_df.to_csv(OUTPUTS_DIR / f"co2_fossil_fuel_extenstions_{name}.csv")

# %% [markdown]
# # Regionalize fossil CO2 (extension, removal disaggregation, regional split)

# %%
# All of the dataframe cleanup, removal disaggregation, gross-positive/CDR
# extension, regional CDR fluxes, regional sector infill and the
# historical/future merge are encapsulated in `regionalize_fossil_co2`.
continuous_timeseries_concise, df_everything = regionalize_fossil_co2(
    fossil_extension_df,
    scenarios_regional,
    df_afolu,
    df_all,
    history,
    fractions_fossil_total,
    cfg.removal_dictionary,
    scenario_model_match,
    future_start_year=FUTURE_START_YEAR,
    scenario_end_year=SCENARIO_END_YEAR,
    extensions_end_year=EXTENSIONS_END_YEAR,
    make_plots=make_plots,
    plots_dir=cfg.plots_dir,
)


# %% [markdown]
# ## Dump per model to database


# %%

# Save per-model CSV files
print("=== SAVING PER-MODEL CSV FILES ===")
for model in df_everything.pix.unique("model"):
    model_data = df_everything.loc[df_everything.index.get_level_values("model") == model]
    output_file = OUTPUTS_DIR / f"extensions_{model.replace(' ', '_').replace('/', '_')}.csv"
    model_data.to_csv(output_file)
    print(f"Saved {model} to {output_file}")


# %% [markdown]
# ## Save to final database
#
# Save both stage="complete" (passthrough from 2100 infilling) and
# stage="extended" (extended markers to 2500) to the final INFILLED_SCENARIOS_DB_EXTENSIONS.

# %%
print("\n=== SAVING FINAL OUTPUT FILES ===")

# Save extended scenarios to CSV (7 markers, 1750-2500)
print("Saving extended scenarios to CSV...")
continuous_timeseries_extended = continuous_timeseries_concise.copy()

# Filter out internal diagnostic variables that aren't part of CMIP7 naming convention
internal_variables = [
    "Emissions|CO2|Gross Positive Emissions",
    "Emissions|CO2|Gross Removals",
]
continuous_timeseries_extended = continuous_timeseries_extended.loc[
    ~continuous_timeseries_extended.index.get_level_values("variable").isin(internal_variables)
]

continuous_timeseries_extended["stage"] = "extended"
continuous_timeseries_extended = continuous_timeseries_extended.set_index("stage", append=True)
continuous_timeseries_extended = continuous_timeseries_extended.droplevel("workflow")
print(continuous_timeseries_extended.index.names)

# Save extended data to CSV
output_file = OUTPUTS_DIR / "extended_scenarios_1750_2500.csv"
continuous_timeseries_extended.to_csv(output_file)
print(f"✅ Saved extended scenarios to {output_file}")
#sys.exit(4)
print(df_everything.pix.unique("scenario"))
print(df_everything.shape)
# %%
# Simple CSV output
if dump_csvs:
    # Execute the simple CSV save
    continuous_file = OUTPUTS_DIR / "continuous_emissions_timeseries_1750_2500.csv"
    continuous_timeseries_concise.to_csv(continuous_file)
    print(f"Saved continuous timeseries to {continuous_file}")
    
    extensions_file = OUTPUTS_DIR / "extensions_full_emissions_timeseries_2023_2500.csv"
    df_everything.to_csv(extensions_file)
    print(f"Saved extensions to {extensions_file}")
    
    complete_file = OUTPUTS_DIR / "scenarios_complete_global_1750_2100.csv"
    scenarios_complete_global.to_csv(complete_file)
    print(f"Saved complete scenarios to {complete_file}")

# %%
scenarios_complete_global.to_csv(OUTPUTS_DIR / "scenarios_complete_global_before_extensions.csv")

# %%
# Generate FaIR-format emissions CSV from the continuous timeseries
from flex.general_utils_for_extensions import convert_continuous_to_fair_csv

_continuous_csv = OUTPUTS_DIR / "continuous_emissions_timeseries_1750_2500.csv"
if _continuous_csv.exists():
    convert_continuous_to_fair_csv(
        str(_continuous_csv),
        str(OUTPUTS_DIR / "emissions_1750-2500.csv"),
        cfg.scenario_model_match,
    )
