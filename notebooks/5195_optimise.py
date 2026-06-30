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
# # Optimize Extension Parameters with FaIR
#
# This notebook optimizes fossil CO2 extension parameters for counterfactual
# scenarios using FaIR to find trajectories that hold temperature constant
# at the departure-year level.
#
# It reads the FaIR-format emissions CSV produced by 5191, loops over every
# entry in `cfg.optimization`, and writes an augmented emissions CSV that
# includes the optimized counterfactual scenarios alongside the originals.

# %%
from pathlib import Path
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from flex.config import load_config, DATA_DIR
from flex.optimise import (
    optimize_scenario,
    run_fair_single_scenario,
    modify_emissions_csv,
    setup_fair,
)

# %% tags=["parameters"]
#config_name = "WIEMIP"
config_name = "vl-frankenstein"
n_jobs = 1  # Number of parallel jobs: 1=sequential, >1=parallel, -1=all cores (capped at 20)

# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir

# Cap n_jobs at 20 when using -1, but allow explicit overrides
if n_jobs == -1:
    n_jobs_effective = min(os.cpu_count() or 1, 20)
    print(f"Auto-detected {os.cpu_count()} cores, capping at {n_jobs_effective} workers")
elif n_jobs > 1:
    n_jobs_effective = n_jobs
    if n_jobs > 20:
        print(f"Using {n_jobs} workers (explicit override of 20-worker default cap)")
    else:
        print(f"Using {n_jobs} parallel workers")
else:
    n_jobs_effective = 1
    print("Sequential mode (1 worker)")

print(f"Config: {cfg.name}")
print(f"Scenarios: {list(cfg.scenario_model_match.keys())}")
print(f"Optimization targets: {list(cfg.optimization.keys())}")

# %% [markdown]
# ## Locate emissions CSV
#
# The optimizer needs the FaIR-format emissions CSV produced by 5191.

# %%
base_emissions_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
if not Path(base_emissions_csv).exists():
    raise FileNotFoundError(
        f"Pipeline-generated emissions not found: {base_emissions_csv}\n"
        "Run 5191 first."
    )
print(f"Base emissions: {base_emissions_csv}")

df_check = pd.read_csv(base_emissions_csv, usecols=["scenario", "variable"])
print(f"Scenarios in CSV: {sorted(df_check['scenario'].unique())}")

# %% [markdown]
# ## Optimise each target scenario
#
# Loop over (or parallelize) every entry in `cfg.optimization`. For each one we:
# 1. Identify the source (non-optimized) marker
# 2. Run baseline FaIR to get the target temperature at the departure year
# 3. Optimise CO2 FFI parameters via `optimize_scenario`
# 4. Write the augmented emissions CSV with the new scenario appended

# %%
timebounds = np.arange(1750, 2501, 1.0)

# Collect markers to optimize
markers_to_optimize = []
for marker, opt_settings in cfg.optimization.items():
    if opt_settings.get("enabled", True):
        markers_to_optimize.append(marker)
    else:
        print(f"Skipping {marker} (disabled)")

print(f"\nWill optimize {len(markers_to_optimize)} marker(s): {markers_to_optimize}")

# Run optimizations in parallel or serial mode
opt_results: dict[str, dict] = {}

if n_jobs_effective > 1 and len(markers_to_optimize) > 1:
    # PARALLEL MODE
    print(f"\n{'='*60}")
    print(f"Running optimizations in PARALLEL with {n_jobs_effective} workers")
    print(f"{'='*60}")
    
    from joblib import Parallel, delayed
    
    def optimize_single_marker(marker, cfg, base_emissions_csv):
        """Wrapper function for parallel execution."""
        print(f"\n{'='*60}")
        print(f"[PARALLEL] Starting optimization: {marker}")
        print(f"{'='*60}")
        
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
    
    parallel_results = Parallel(n_jobs=n_jobs_effective, verbose=10)(
        delayed(optimize_single_marker)(marker, cfg, base_emissions_csv)
        for marker in markers_to_optimize
    )
    
    opt_results = {marker: result for marker, result in parallel_results}
    
    print(f"\n{'='*60}")
    print(f"All {len(opt_results)} optimizations complete!")
    print(f"{'='*60}")
    
else:
    # SEQUENTIAL MODE
    if n_jobs_effective > 1:
        print(f"\nNote: Only {len(markers_to_optimize)} scenario(s) to optimize - running sequentially")
    
    for marker in markers_to_optimize:
        print(f"\n{'='*60}")
        print(f"Optimizing: {marker}")
        print(f"{'='*60}")


        result = optimize_scenario(
            cfg,
            marker=marker,
            base_emissions_csv=base_emissions_csv,
            memory_limited=True,
        )
        opt_results[marker] = result
        
        print(f"\nOptimized ECS params for {marker}:")
        print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr (total CO2)")
        print(f"  sig_start = {result['sig_start']:.0f}")
        print(f"  sig_end   = {result['sig_end']:.0f}")
        print(f"  Target T  = {result['target_temp']:.4f} K")
        print(f"  Departure = {result['departure_year']}")
        print(f"  Final cost = {result['final_cost']:.6f}")

# %% [markdown]
# ## Save optimization results
#
# Write the optimized parameters to JSON for use in the next step (5196_apply_optimised)

# %%
import json

results_file = OUTPUTS_DIR / "optimization_results.json"

# Convert results to serializable format
results_data = {
    "config": config_name,
    "optimization_results": {}
}

for marker, result in opt_results.items():
    results_data["optimization_results"][marker] = {
        "exp_targ": float(result["exp_targ"]),
        "sig_start": float(result["sig_start"]),
        "sig_end": float(result["sig_end"]),
        "target_temp": float(result["target_temp"]),
        "departure_year": int(result["departure_year"]),
        "final_cost": float(result["final_cost"]),
        "success": bool(result["success"]),
        "message": str(result.get("message", "")),
    }

with open(results_file, "w") as f:
    json.dump(results_data, f, indent=2)

print(f"\nOptimization results saved to: {results_file}")

# %% [markdown]
# ## Summary
#
# Print a summary table of the optimization results

# %%
print(f"\n{'='*80}")
print("OPTIMIZATION SUMMARY")
print(f"{'='*80}")
summary_data = []
for marker, result in opt_results.items():
    summary_data.append({
        'Marker': marker,
        'Departure': result['departure_year'],
        'Target T (K)': f"{result['target_temp']:.4f}",
        'exp_targ': f"{result['exp_targ']:.0f}",
        'sig_start': f"{result['sig_start']:.0f}",
        'sig_end': f"{result['sig_end']:.0f}",
        'Cost': f"{result['final_cost']:.6f}",
        'Success': result['success'],
    })

df_summary = pd.DataFrame(summary_data)
print(df_summary.to_string(index=False))
print(f"{'='*80}")
print(f"\nNext step: Run 5196_apply_optimised to generate emissions files with these parameters")

