# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Apply Optimized Parameters to Generate Emissions
#
# This notebook reads the optimization results from `5195_optimise` and applies
# the optimized CO2 parameters to generate counterfactual emissions scenarios.
#
# It then verifies the results by running FaIR simulations and generates
# diagnostic plots comparing the optimized scenarios to their source markers.

# %%
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from flex.config import load_config, DATA_DIR
from flex.optimise import (
    modify_emissions_csv,
    setup_fair,
)

# %% tags=["parameters"]
config_name = "WIEMIP"

# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir

print(f"Config: {cfg.name}")
print(f"Scenarios: {list(cfg.scenario_model_match.keys())}")

# %% [markdown]
# ## Load optimization results
#
# Read the optimized parameters from the JSON file created by 5195_optimise

# %%
results_file = OUTPUTS_DIR / "optimization_results.json"

if not results_file.exists():
    raise FileNotFoundError(
        f"Optimization results not found: {results_file}\n"
        "Run 5195_optimise first to generate optimized parameters."
    )

with open(results_file, "r") as f:
    results_data = json.load(f)

if results_data["config"] != config_name:
    print(f"WARNING: Optimization results are from config '{results_data['config']}', "
          f"but currently using '{config_name}'")

opt_results = results_data["optimization_results"]

print(f"\nLoaded optimization results for {len(opt_results)} scenario(s):")
for marker in opt_results:
    print(f"  - {marker}")

# %% [markdown]
# ## Locate base emissions CSV
#
# This is the emissions CSV from 5191, before optimization

# %%
base_emissions_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
if not Path(base_emissions_csv).exists():
    raise FileNotFoundError(
        f"Base emissions not found: {base_emissions_csv}\n"
        "Run 5191 first."
    )
print(f"Base emissions: {base_emissions_csv}")

# %% [markdown]
# ## Apply optimized parameters to generate emissions
#
# For each optimized scenario, build the CO2 FFI trajectory using the
# optimized parameters and append it to the emissions CSV

# %%
current_csv = base_emissions_csv

for marker, result in opt_results.items():
    print(f"\nApplying optimized parameters for: {marker}")
    print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr")
    print(f"  sig_start = {result['sig_start']:.0f}")
    print(f"  sig_end   = {result['sig_end']:.0f}")
    print(f"  departure = {result['departure_year']}")
    
    # Find the source marker (first non-optimized marker sharing scenario+model)
    source_marker = None
    base_scenario = cfg.scenario_model_match[marker][0]
    for m, info in cfg.scenario_model_match.items():
        if m != marker and info[0] == base_scenario and info[1] == cfg.scenario_model_match[marker][1]:
            source_marker = m
            break
    
    if source_marker is None:
        raise ValueError(f"No source marker found for {marker}")
    
    print(f"  source    = {source_marker}")
    
    # Read emissions data
    df_emis = pd.read_csv(current_csv)
    source_ffi = df_emis[(df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 FFI")]
    source_afolu = df_emis[(df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 AFOLU")]
    year_cols = [c for c in df_emis.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    co2_ffi = source_ffi[year_cols].values.flatten().copy()
    co2_afolu = source_afolu[year_cols].values.flatten().copy() if len(source_afolu) else np.zeros_like(co2_ffi)
    
    # Build optimized CO2 FFI trajectory
    departure_year = result["departure_year"]
    dep_idx_emis = np.searchsorted(years, departure_year + 0.5)
    exp_targ = result["exp_targ"]
    sig_start = result["sig_start"]
    sig_end = result["sig_end"]
    exp_end = int(sig_start)
    
    # Build total CO2 (FFI + AFOLU) trajectory, then derive FFI
    total_co2 = (co2_ffi + co2_afolu).copy()
    dep_value = total_co2[dep_idx_emis]
    
    for i in range(dep_idx_emis, len(total_co2)):
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            # Linear ramp to exp_targ
            frac = (years[i] - departure_year) / yr_total
            total_co2[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            # Hold at exp_targ
            total_co2[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            # Smoothstep to zero
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3
            total_co2[i] = exp_targ * (1 - s)
        else:
            # Zero emissions
            total_co2[i] = 0.0
    
    # Derive CO2 FFI = total - AFOLU
    co2_opt = co2_ffi.copy()
    co2_opt[dep_idx_emis:] = total_co2[dep_idx_emis:] - co2_afolu[dep_idx_emis:]
    
    # Write to emissions CSV
    final_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
    modify_emissions_csv(
        current_csv, source_marker, marker,
        co2_ffi_trajectory=co2_opt,
        departure_year=departure_year,
        output_path=final_csv,
    )
    current_csv = final_csv

print(f"\nAll scenarios applied. Augmented CSV: {current_csv}")

# %% [markdown]
# ## Verification: run all scenarios through FaIR
#
# Run FaIR simulations on all scenarios (original + optimized) to verify
# that the optimized scenarios achieve their temperature targets

# %%
all_scenarios = sorted(pd.read_csv(current_csv, usecols=["scenario"])["scenario"].unique())
print(f"\nVerifying {len(all_scenarios)} scenarios through FaIR:")
print(f"  {all_scenarios}")

# Use the same n_configs as optimization for consistency
# Take n_configs from the first optimization entry
n_configs = None
if opt_results:
    first_marker = list(opt_results.keys())[0]
    if first_marker in cfg.optimization:
        n_configs = cfg.optimization[first_marker].get("n_configs", None)

if n_configs is not None:
    print(f"Using n_configs={n_configs} (from optimization settings)")
    f = setup_fair(
        current_csv, all_scenarios,
        n_configs=n_configs,
        scenario_mapping={**cfg.scenario_mapping, **cfg.forcing_scenario},
        fair_calib_version = cfg.fair_calibration_version,
    )
else:
    print(f"Using memory_limited ensemble (5 members)")
    f = setup_fair(
        current_csv, all_scenarios,
        memory_limited=True,
        scenario_mapping={**cfg.scenario_mapping, **cfg.forcing_scenario},
    )

f.run()

print("\nFaIR simulations complete")

# Get timebounds from FaIR output (to ensure dimension matching)
timebounds = f.timebounds

# %% [markdown]
# ## Diagnostic plots
#
# For each optimized scenario, plot:
# 1. Temperature: source vs optimized vs target
# 2. CO2 FFI emissions: source vs optimized 
# 3. Cumulative CO2 FFI: source vs optimized

# %%
for marker, result in opt_results.items():
    # Find source marker
    source_marker = None
    base_scenario = cfg.scenario_model_match[marker][0]
    for m, info in cfg.scenario_model_match.items():
        if m != marker and info[0] == base_scenario and info[1] == cfg.scenario_model_match[marker][1]:
            source_marker = m
            break
    
    departure_year = result["departure_year"]
    target_temp = result["target_temp"]
    source_color = cfg.scenario_model_match[source_marker][2]
    marker_color = cfg.scenario_model_match[marker][2]
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # Temperature
    ax = axes[0]
    source_temp = f.temperature.sel(scenario=source_marker, layer=0).median(dim="config").values
    opt_temp = f.temperature.sel(scenario=marker, layer=0).median(dim="config").values
    ax.plot(timebounds, source_temp, label=source_marker, color=source_color, linewidth=2)
    ax.plot(timebounds, opt_temp, label=marker, color=marker_color, linewidth=2)
    ax.axhline(target_temp, color='red', linestyle='--', linewidth=1, label=f'Target ({target_temp:.2f} K)')
    ax.axvline(departure_year, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlim(1900, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature (K)")
    ax.set_title(f"{marker} vs {source_marker}: Temperature")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # CO2 FFI
    ax = axes[1]
    df_plot = pd.read_csv(current_csv)
    source_ffi_plot = df_plot[(df_plot["scenario"] == source_marker) & (df_plot["variable"] == "CO2 FFI")]
    opt_ffi_plot = df_plot[(df_plot["scenario"] == marker) & (df_plot["variable"] == "CO2 FFI")]
    year_cols_plot = [c for c in df_plot.columns if c.replace(".", "").replace("-", "").isdigit()]
    years_plot = np.array([float(c) for c in year_cols_plot])
    
    if len(source_ffi_plot):
        ax.plot(years_plot, source_ffi_plot[year_cols_plot].values.flatten(),
                label=source_marker, color=source_color, linewidth=2)
    if len(opt_ffi_plot):
        ax.plot(years_plot, opt_ffi_plot[year_cols_plot].values.flatten(),
                label=marker, color=marker_color, linewidth=2)
    ax.axvline(departure_year, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlim(1900, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 FFI (Mt CO2/yr)")
    ax.set_title(f"{marker} vs {source_marker}: CO2 FFI")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Cumulative emissions
    ax = axes[2]
    source_cum = f.cumulative_emissions.sel(scenario=source_marker, specie="CO2 FFI").mean(dim="config").values
    opt_cum = f.cumulative_emissions.sel(scenario=marker, specie="CO2 FFI").mean(dim="config").values
    ax.plot(timebounds, source_cum, label=source_marker, color=source_color, linewidth=2)
    ax.plot(timebounds, opt_cum, label=marker, color=marker_color, linewidth=2)
    ax.axvline(departure_year, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlim(1900, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative CO2 FFI (Gt CO2)")
    ax.set_title(f"{marker} vs {source_marker}: Cumulative CO2 FFI")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / f"optimization_{marker}_verification.png", dpi=150, bbox_inches='tight')
    plt.show()

# %%
# Print final summary comparing target vs achieved temperatures
print(f"\n{'='*80}")
print("VERIFICATION SUMMARY")
print(f"{'='*80}")
verification_data = []

for marker, result in opt_results.items():
    opt_temp = f.temperature.sel(scenario=marker, layer=0).mean(dim="config").values
    departure_year = result["departure_year"]
    target_temp = result["target_temp"]
    
    # Calculate post-departure temperature statistics
    dep_bound_idx = int(np.searchsorted(timebounds, departure_year))
    post_dep_temp = opt_temp[dep_bound_idx:]
    
    mean_temp = np.mean(post_dep_temp)
    max_temp = np.max(post_dep_temp)
    min_temp = np.min(post_dep_temp)
    temp_range = max_temp - min_temp
    
    verification_data.append({
        'Marker': marker,
        'Target T (K)': f"{target_temp:.4f}",
        'Mean T (K)': f"{mean_temp:.4f}",
        'Min T (K)': f"{min_temp:.4f}",
        'Max T (K)': f"{max_temp:.4f}",
        'Range (K)': f"{temp_range:.4f}",
        'Error': f"{abs(mean_temp - target_temp):.4f}",
    })

df_verify = pd.DataFrame(verification_data)
print(df_verify.to_string(index=False))
print(f"{'='*80}")
