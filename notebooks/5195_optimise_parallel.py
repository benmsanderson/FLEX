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
# # Optimize Extension Parameters with FaIR (Parallel Version)
#
# This notebook optimizes fossil CO2 extension parameters for counterfactual
# scenarios using FaIR to find trajectories that hold temperature constant
# at the departure-year level.
#
# **PARALLEL VERSION**: Runs multiple scenario optimizations in parallel using
# joblib to exploit cluster resources.
#
# It reads the FaIR-format emissions CSV produced by 5191, loops over every
# entry in `cfg.optimization`, and writes an augmented emissions CSV that
# includes the optimized counterfactual scenarios alongside the originals.

# %%
from pathlib import Path
from functools import partial
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from flex.config import load_config, DATA_DIR
from flex.optimise import (
    optimize_scenario,
    run_fair_single_scenario,
    modify_emissions_csv,
    setup_fair,
)

# %% tags=["parameters"]
config_name = "WIEMIP"
n_jobs = -1  # Use all available cores (-1), or specify a number

# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir

# Cap n_jobs at 20 when using -1, but allow explicit overrides
if n_jobs == -1:
    n_jobs_effective = min(os.cpu_count() or 1, 20)
    print(
        f"Auto-detected {os.cpu_count()} cores, capping at {n_jobs_effective} workers"
    )
else:
    n_jobs_effective = n_jobs
    if n_jobs > 20:
        print(f"Using {n_jobs} workers (explicit override of 20-worker default cap)")

print(f"Config: {cfg.name}")
print(f"Scenarios: {list(cfg.scenario_model_match.keys())}")
print(f"Optimization targets: {list(cfg.optimization.keys())}")
print(f"Parallel jobs: {n_jobs_effective}")

# %% [markdown]
# ## Locate emissions CSV
#
# The optimizer needs the FaIR-format emissions CSV produced by 5191.

# %%
base_emissions_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
if not Path(base_emissions_csv).exists():
    raise FileNotFoundError(
        f"Pipeline-generated emissions not found: {base_emissions_csv}\nRun 5191 first."
    )
print(f"Base emissions: {base_emissions_csv}")

df_check = pd.read_csv(base_emissions_csv, usecols=["scenario", "variable"])
print(f"Scenarios in CSV: {sorted(df_check['scenario'].unique())}")

# %% [markdown]
# ## Prepare optimization tasks
#
# Collect all enabled optimization tasks that can be run independently

# %%
timebounds = np.arange(1750, 2501, 1.0)

# Collect markers to optimize
markers_to_optimize = []
for marker, opt_settings in cfg.optimization.items():
    if opt_settings.get("enabled", True):
        markers_to_optimize.append(marker)
    else:
        print(f"Skipping {marker} (disabled)")

print(
    f"\nWill optimize {len(markers_to_optimize)} markers in parallel: {markers_to_optimize}"
)

# %% [markdown]
# ## Run optimizations in parallel
#
# Use joblib to parallelize the independent optimization tasks


# %%
def optimize_single_marker(marker, cfg, base_emissions_csv):
    """Wrapper function for parallel execution."""
    print(f"\n{'=' * 60}")
    print(f"[PARALLEL] Starting optimization: {marker}")
    print(f"{'=' * 60}")

    result = optimize_scenario(
        cfg,
        marker=marker,
        base_emissions_csv=base_emissions_csv,
        memory_limited=True,
    )

    print(f"\n[PARALLEL] Completed {marker}:")
    print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr (total CO2)")
    print(f"  sig_start = {result['sig_start']:.0f}")
    print(f"  sig_end   = {result['sig_end']:.0f}")
    print(f"  Target T  = {result['target_temp']:.4f} K")
    print(f"  Departure = {result['departure_year']}")
    print(f"  Final cost = {result['final_cost']:.6f}")

    return marker, result


# Run optimizations in parallel
print(f"\nStarting parallel optimization with {n_jobs_effective} jobs...")
parallel_results = Parallel(n_jobs=n_jobs_effective, verbose=10)(
    delayed(optimize_single_marker)(marker, cfg, base_emissions_csv)
    for marker in markers_to_optimize
)

# Convert to dictionary
opt_results = {marker: result for marker, result in parallel_results}

print(f"\n{'=' * 60}")
print(f"All {len(opt_results)} optimizations complete!")
print(f"{'=' * 60}")

# %% [markdown]
# ## Write optimized scenarios to CSV
#
# Now append each optimized scenario to the emissions CSV

# %%
current_csv = base_emissions_csv

for marker in markers_to_optimize:
    result = opt_results[marker]

    print(f"\nWriting optimized scenario: {marker}")

    # --- Build the optimized CO2 trajectory and append to CSV ---
    departure_year = result["departure_year"]

    # Find the source marker (first non-optimized marker sharing scenario+model)
    source_marker = None
    base_scenario = cfg.scenario_model_match[marker][0]
    for m, info in cfg.scenario_model_match.items():
        if (
            m != marker
            and info[0] == base_scenario
            and info[1] == cfg.scenario_model_match[marker][1]
        ):
            source_marker = m
            break

    df_emis = pd.read_csv(current_csv)
    source_ffi = df_emis[
        (df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 FFI")
    ]
    source_afolu = df_emis[
        (df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 AFOLU")
    ]
    year_cols = [
        c for c in df_emis.columns if c.replace(".", "").replace("-", "").isdigit()
    ]
    years = np.array([float(c) for c in year_cols])
    co2_ffi = source_ffi[year_cols].values.flatten().copy()
    co2_afolu = (
        source_afolu[year_cols].values.flatten().copy()
        if len(source_afolu)
        else np.zeros_like(co2_ffi)
    )

    dep_idx_emis = np.searchsorted(years, departure_year + 0.5)
    exp_targ = result["exp_targ"]
    sig_start = result["sig_start"]
    sig_end = result["sig_end"]
    exp_end = int(sig_start)

    # Build total CO2 trajectory, derive FFI = total - AFOLU
    total_co2 = (co2_ffi + co2_afolu).copy()
    dep_value = total_co2[dep_idx_emis]

    for i in range(dep_idx_emis, len(total_co2)):
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            frac = (years[i] - departure_year) / yr_total
            total_co2[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            total_co2[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3
            total_co2[i] = exp_targ * (1 - s)
        else:
            total_co2[i] = 0.0

    co2_opt = co2_ffi.copy()
    co2_opt[dep_idx_emis:] = total_co2[dep_idx_emis:] - co2_afolu[dep_idx_emis:]

    final_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
    modify_emissions_csv(
        current_csv,
        source_marker,
        marker,
        co2_ffi_trajectory=co2_opt,
        departure_year=departure_year,
        output_path=final_csv,
    )
    current_csv = final_csv

print(f"\nAll optimizations complete. Augmented CSV: {current_csv}")

# %% [markdown]
# ## Verification: run all optimized scenarios through FaIR

# %%
# Build list of all scenarios for the verification run
all_scenarios = sorted(
    pd.read_csv(current_csv, usecols=["scenario"])["scenario"].unique()
)
print(f"Verifying scenarios: {all_scenarios}")

f = setup_fair(
    current_csv,
    all_scenarios,
    memory_limited=True,
    scenario_mapping={**cfg.scenario_mapping, **cfg.forcing_scenario},
)
f.run()

# %%
# Summary table
print("\n" + "=" * 80)
print("OPTIMIZATION SUMMARY")
print("=" * 80)
summary_data = []
for marker, result in opt_results.items():
    summary_data.append(
        {
            "Marker": marker,
            "Departure Year": result["departure_year"],
            "Target Temp (K)": f"{result['target_temp']:.4f}",
            "exp_targ (Mt CO2/yr)": f"{result['exp_targ']:.0f}",
            "sig_start": f"{result['sig_start']:.0f}",
            "sig_end": f"{result['sig_end']:.0f}",
            "Final Cost": f"{result['final_cost']:.6f}",
            "Success": result["success"],
        }
    )

df_summary = pd.DataFrame(summary_data)
print(df_summary.to_string(index=False))
print("=" * 80)
