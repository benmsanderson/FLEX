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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from flex.config import load_config, DATA_DIR
from flex.optimise import (
    optimize_scenario,
    run_fair_single_scenario,
    modify_emissions_csv,
    build_ch4_plateau_trajectory,
    setup_fair,
)

# %% tags=["parameters"]
config_name = "WIEMIP"

# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir
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
# Loop over every entry in `cfg.optimization`. For each one we:
# 1. Identify the source (non-optimized) marker
# 2. Run baseline FaIR to get the target temperature at the departure year
# 3. Optimise CO2 FFI parameters via `optimize_scenario`
# 4. Write the augmented emissions CSV with the new scenario appended

# %%
timebounds = np.arange(1750, 2501, 1.0)

# We'll accumulate results and progressively augment the CSV
current_csv = base_emissions_csv
opt_results: dict[str, dict] = {}

for marker, opt_settings in cfg.optimization.items():
    if not opt_settings.get("enabled", True):
        print(f"Skipping {marker} (disabled)")
        continue

    print(f"\n{'='*60}")
    print(f"Optimizing: {marker}")
    print(f"{'='*60}")

    result = optimize_scenario(
        cfg,
        marker=marker,
        base_emissions_csv=current_csv,
        memory_limited=True,
    )
    opt_results[marker] = result

    print(f"\nOptimized ECS params for {marker}:")
    print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr")
    print(f"  sig_start = {result['sig_start']:.0f}")
    print(f"  sig_end   = {result['sig_end']:.0f}")
    print(f"  Target T  = {result['target_temp']:.4f} K")
    print(f"  Final cost = {result['final_cost']:.6f}")

    # --- Build the optimized CO2 trajectory and append to CSV ---
    departure_year = opt_settings["departure_year"]
    ch4_traj = result["ch4_trajectory"]

    # Find the source marker (first non-optimized marker sharing scenario+model)
    source_marker = None
    base_scenario = cfg.scenario_model_match[marker][0]
    for m, info in cfg.scenario_model_match.items():
        if m != marker and info[0] == base_scenario and info[1] == cfg.scenario_model_match[marker][1]:
            source_marker = m
            break

    df_emis = pd.read_csv(current_csv)
    source = df_emis[(df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 FFI")]
    year_cols = [c for c in df_emis.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    co2_opt = source[year_cols].values.flatten().copy()

    dep_idx_emis = np.searchsorted(years, departure_year + 0.5)
    dep_value = co2_opt[dep_idx_emis]
    exp_targ = result["exp_targ"]
    sig_start = result["sig_start"]
    sig_end = result["sig_end"]
    exp_end = int(sig_start)

    for i in range(dep_idx_emis, len(co2_opt)):
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            frac = (years[i] - departure_year) / yr_total
            co2_opt[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            co2_opt[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3
            co2_opt[i] = exp_targ * (1 - s)
        else:
            co2_opt[i] = 0.0

    final_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
    modify_emissions_csv(
        current_csv, source_marker, marker,
        co2_ffi_trajectory=co2_opt,
        ch4_trajectory=ch4_traj,
        departure_year=departure_year,
        output_path=final_csv,
    )
    current_csv = final_csv

print(f"\nAll optimizations complete. Augmented CSV: {current_csv}")

# %% [markdown]
# ## Verification: run all optimized scenarios through FaIR

# %%
# Build list of all scenarios for the verification run
all_scenarios = sorted(pd.read_csv(current_csv, usecols=["scenario"])["scenario"].unique())
print(f"Verifying scenarios: {all_scenarios}")

f = setup_fair(
    current_csv, all_scenarios,
    memory_limited=True,
    scenario_mapping={**cfg.scenario_mapping, **cfg.forcing_scenario},
)
f.run()

# %%
# Plot each optimized marker vs its source
for marker, result in opt_results.items():
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
    for scen, color in [(source_marker, source_color), (marker, marker_color)]:
        temp = f.temperature.sel(scenario=scen, layer=0)
        median = temp.median(dim="config").values
        p05 = temp.quantile(0.05, dim="config").values
        p95 = temp.quantile(0.95, dim="config").values
        tb = np.arange(1750, 2502, 1.0)
        ax.plot(tb, median, color=color, label=scen)
        ax.fill_between(tb, p05, p95, color=color, alpha=0.15)
    ax.axhline(target_temp, color="gray", ls="--", alpha=0.5)
    ax.axvline(departure_year, color="red", ls="--", alpha=0.3)
    ax.set_xlim(2000, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature anomaly (K)")
    ax.set_title("Temperature")
    ax.legend()

    # CO2 FFI emissions
    ax = axes[1]
    for scen, color in [(source_marker, source_color), (marker, marker_color)]:
        co2 = f.emissions.sel(scenario=scen, specie="CO2 FFI", config=f.configs[0]).values
        ax.plot(f.timepoints, co2, color=color, label=scen)
    ax.axvline(departure_year, color="red", ls="--", alpha=0.3)
    ax.set_xlim(2000, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 FFI (Mt/yr)")
    ax.set_title("CO2 FFI Emissions")
    ax.legend()

    # CH4 emissions
    ax = axes[2]
    for scen, color in [(source_marker, source_color), (marker, marker_color)]:
        ch4 = f.emissions.sel(scenario=scen, specie="CH4", config=f.configs[0]).values
        ax.plot(f.timepoints, ch4, color=color, label=scen)
    ax.axvline(departure_year, color="red", ls="--", alpha=0.3)
    ax.set_xlim(2000, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("CH4 (Mt/yr)")
    ax.set_title("CH4 Emissions")
    ax.legend()

    plt.suptitle(
        f"{source_marker} vs {marker} (departure {departure_year}, target {target_temp:.2f} K)",
        fontsize=14,
    )
    plt.tight_layout()
    plt.savefig(cfg.plots_dir / f"{marker}_optimization_result.png", dpi=150)
    plt.show()

print("Done!")
