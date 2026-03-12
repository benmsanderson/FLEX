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
# **HL-CF**: Departs from HL at 2080, adjusts CO2 and CH4 so median
# temperature stays at the 2080 peak rather than declining.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src directory to path
src_dir = Path().resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from flex.config import load_config, DATA_DIR
from flex.optimise import (
    optimize_scenario,
    run_fair_single_scenario,
    modify_emissions_csv,
    build_ch4_plateau_trajectory,
)

# %% tags=["parameters"]
config_name = "WIEMIP"

# %%
cfg = load_config(config_name)
print(f"Config: {cfg.name}")
print(f"Scenarios: {list(cfg.scenario_model_match.keys())}")
print(f"Optimization targets: {list(cfg.optimization.keys())}")

# %% [markdown]
# ## Locate emissions CSV
#
# The optimizer needs the FaIR-format emissions CSV. This should already
# exist from a prior run of the extension pipeline (5191) for the
# scenariomip_default config, or from the data/fair-inputs directory.

# %%
# Use the standard FaIR emissions as the base
# (contains all 7 ScenarioMIP markers, 1750-2500)
base_emissions_csv = str(DATA_DIR / "fair-inputs" / "emissions_1750-2500.csv")
print(f"Base emissions: {base_emissions_csv}")

# Verify it exists and has HL
df_check = pd.read_csv(base_emissions_csv, usecols=["scenario", "variable"])
print(f"Scenarios in CSV: {sorted(df_check['scenario'].unique())}")

# %% [markdown]
# ## Run baseline HL through FaIR
#
# First, run the standard HL scenario to see the temperature trajectory
# we're trying to modify.

# %%
print("Running baseline HL through FaIR (memory_limited)...")
temp_baseline_hl = run_fair_single_scenario(
    base_emissions_csv, "HL", memory_limited=True
)

# FaIR returns 752 values (timebound boundaries 1750.0–2501.0);
# trim to 751 to match year-centred timebounds
timebounds = np.arange(1750, 2501, 1.0)
temp_baseline_hl = temp_baseline_hl[:len(timebounds)]
departure_year = cfg.optimization["HL-CF"]["departure_year"]
dep_idx = np.searchsorted(timebounds, departure_year)
target_temp = temp_baseline_hl[dep_idx]

print(f"HL temperature at {departure_year}: {target_temp:.4f} K above pre-industrial")
print(f"HL peak temperature: {temp_baseline_hl.max():.4f} K at year {timebounds[temp_baseline_hl.argmax()]:.0f}")

# %%
# Quick plot of baseline HL temperature
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(timebounds, temp_baseline_hl, label="HL baseline", color=cfg.plot_colors["HL"])
ax.axhline(target_temp, color="gray", ls="--", alpha=0.7, label=f"Target ({target_temp:.2f} K)")
ax.axvline(departure_year, color="red", ls="--", alpha=0.5, label=f"Departure ({departure_year})")
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly (K)")
ax.set_xlim(1900, 2500)
ax.legend()
ax.set_title("HL baseline temperature — target for HL-CF")
plt.tight_layout()
plt.savefig(cfg.plots_dir / "hl_baseline_temperature.png", dpi=150)
plt.show()

# %% [markdown]
# ## Run optimization
#
# Search over `[exp_targ, sig_start, sig_end]` to find CO2 FFI extension
# parameters that hold temperature at the departure-year level.

# %%
print("Starting optimization for HL-CF...")
result = optimize_scenario(
    cfg,
    marker="HL-CF",
    base_emissions_csv=base_emissions_csv,
    memory_limited=True,
)

print(f"\nOptimized ECS params for HL-CF:")
print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr")
print(f"  sig_start = {result['sig_start']:.0f}")
print(f"  sig_end   = {result['sig_end']:.0f}")
print(f"  Target T  = {result['target_temp']:.4f} K")
print(f"  Final cost = {result['final_cost']:.6f}")

# %% [markdown]
# ## Verify: run optimized HL-CF through FaIR

# %%
# Build the optimized emissions CSV
ch4_traj = result["ch4_trajectory"]

# Rebuild CO2 trajectory with optimized params
df_emis = pd.read_csv(base_emissions_csv)
source = df_emis[(df_emis["scenario"] == "HL") & (df_emis["variable"] == "CO2 FFI")]
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

final_csv = str(cfg.outputs_dir / "emissions_1750-2500.csv")
modify_emissions_csv(
    base_emissions_csv, "HL", "HL-CF",
    co2_ffi_trajectory=co2_opt,
    ch4_trajectory=ch4_traj,
    departure_year=departure_year,
    output_path=final_csv,
)

# Run FaIR with both HL and HL-CF
# HL-CF needs scenario_mapping so it inherits HL's volcanic/solar forcing
from flex.optimise import setup_fair
f = setup_fair(
    final_csv, ["HL", "HL-CF"],
    memory_limited=True,
    scenario_mapping={"HL-CF": "HL"},
)
f.run()

# %%
# Plot comparison
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Temperature
ax = axes[0]
for scen, color in [("HL", cfg.plot_colors["HL"]), ("HL-CF", cfg.plot_colors["HL-CF"])]:
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
for scen, color in [("HL", cfg.plot_colors["HL"]), ("HL-CF", cfg.plot_colors["HL-CF"])]:
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
for scen, color in [("HL", cfg.plot_colors["HL"]), ("HL-CF", cfg.plot_colors["HL-CF"])]:
    ch4 = f.emissions.sel(scenario=scen, specie="CH4", config=f.configs[0]).values
    ax.plot(f.timepoints, ch4, color=color, label=scen)
ax.axvline(departure_year, color="red", ls="--", alpha=0.3)
ax.set_xlim(2000, 2500)
ax.set_xlabel("Year")
ax.set_ylabel("CH4 (Mt/yr)")
ax.set_title("CH4 Emissions")
ax.legend()

plt.suptitle(f"HL vs HL-CF (departure {departure_year}, target {target_temp:.2f} K)", fontsize=14)
plt.tight_layout()
plt.savefig(cfg.plots_dir / "hl_cf_optimization_result.png", dpi=150)
plt.show()

print("Done!")
