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
# # FaIR Climate Model Results Visualization
#
# This notebook loads precomputed FaIR model outputs from the simulation notebook (5201) and creates comprehensive visualizations.
#
# **Inputs:** CSV files from `outputs/` directory
# - `fair_temperature_1750-2500.csv` - Temperature projections
# - `fair_forcing_1750-2500.csv` - Radiative forcing by species
# - `fair_concentration_ghgs_1750-2500.csv` - GHG concentrations
# - `fair_co2e_emissions_1750-2500.csv` - CO2-equivalent emissions
#
# **Outputs:** Figures saved to `plots/` directory

# %%
import os
import sys
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as pl
import numpy as np
import pandas as pd

# Add src directory to path
src_dir = Path().resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from flex.config import load_config

# %% tags=["parameters"]
config_name = "scenariomip_default"

# --- Ensemble configuration ---
# %%
cfg = load_config(config_name)
OUTPUTS_DIR = cfg.outputs_dir
PLOTS_DIR = cfg.plots_dir
print(f"Config: {cfg.name}")
print(f"Reading from: {OUTPUTS_DIR}")
print(f"Saving to: {PLOTS_DIR}")

# %% [markdown]
# ## Load Climate Model Outputs

# %%
# Load temperature data
temp_df = pd.read_csv(OUTPUTS_DIR / 'fair_temperature_1750-2500.csv')
print(f"Temperature data: {len(temp_df)} rows")

# Load forcing data
forcing_df = pd.read_csv(OUTPUTS_DIR / 'fair_forcing_1750-2500.csv')
print(f"Forcing data: {len(forcing_df)} rows")

# Load concentration data
conc_df = pd.read_csv(OUTPUTS_DIR / 'fair_concentration_ghgs_1750-2500.csv')
print(f"Concentration data: {len(conc_df)} rows")

# Load CO2e emissions
co2e_df = pd.read_csv(OUTPUTS_DIR / 'fair_co2e_emissions_1750-2500.csv')
print(f"CO2e emissions: {len(co2e_df)} rows")

# %% [markdown]
# ## Setup: Scenario Names and Colors

# %%
# Scenario names
scenario_model_match = cfg.scenario_model_match

# %%
# Load additional data files for plotting
emis_species_df = pd.read_csv(OUTPUTS_DIR / 'fair_emissions_by_species.csv')
forcing_sum_df = pd.read_csv(OUTPUTS_DIR / 'fair_forcing_sum_1750-2500.csv')
ecdf_df = pd.read_csv(OUTPUTS_DIR / 'fair_temperature_ecdf_data.csv')

print(f"Emissions by species: {len(emis_species_df)} rows")
print(f"Total forcing: {len(forcing_sum_df)} rows")
print(f"ECDF data: {len(ecdf_df)} rows")

# %% [markdown]
# ## Plot 1: Temperature & Emissions Combined (temperature_emis.png)
#
# Side-by-side visualization showing:
# - **Left panel:** CO2-equivalent emissions with uncertainty bands (IAM scenarios 2025-2100, extensions 2101-2150)
# - **Right panel:** Temperature anomalies relative to 1850-1900 baseline with 5th-95th percentile ranges

# %%
fig, ax = pl.subplots(1, 2, figsize=(12, 5))

# Calculate uncertainty band (simplified hyperbolic tangent scaling)
# Requires both VL and H scenarios; skip if not available.
_available = set(co2e_df['Scenario'].unique())
if 'VL' in _available and 'H' in _available:
    co2e_vl = co2e_df[co2e_df['Scenario'] == 'VL'].set_index('Year')['CO2e_emissions']
    co2e_h = co2e_df[co2e_df['Scenario'] == 'H'].set_index('Year')['CO2e_emissions']
    unc = np.tanh((co2e_vl - co2e_h) / 1e6 / 10) * 8
else:
    unc = None

# Left panel: CO2e emissions with uncertainty
for scenario, meta in scenario_model_match.items():
    scenario_data = co2e_df[co2e_df['Scenario'] == scenario].set_index('Year')
    years = scenario_data.index.values
    emissions = scenario_data['CO2e_emissions'].values / 1e6
    
    # Historical period (up to year 2100)
    hist_mask = years <= 2100
    if unc is not None:
        ax[0].fill_between(
            years[hist_mask],
            emissions[hist_mask] - unc.values[hist_mask],
            emissions[hist_mask] + unc.values[hist_mask],
            color=meta[2],
            lw=0,
            alpha=0.3,
        )
    
    # Extension period (2100+)
    ext_mask = years >= 2100
    if unc is not None:
        ax[0].fill_between(
            years[ext_mask],
            emissions[ext_mask] - unc.values[ext_mask],
            emissions[ext_mask] + unc.values[ext_mask],
            color=meta[2],
            hatch="XXX",
            lw=0,
            alpha=0.1,
        )
    
    # Historical line (up to 2024)
    hist_line_mask = years <= 2024
    ax[0].plot(
        years[hist_line_mask],
        emissions[hist_line_mask],
        color="k",
    )


ax[0].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")
ax[0].axhline(ls=":", color="k", lw=0.5)
ax[0].set_xlim(2000, 2150)
ax[0].set_ylim(-50, 100)
ax[0].grid()
ax[0].set_title("(a)")

# Right panel: Temperature anomalies
for scenario, meta in scenario_model_match.items():
    print(meta)
    scenario_temp = temp_df[temp_df['Scenario'] == scenario]
    years = scenario_temp['Year'].values
    
    # Calculate anomaly relative to 1850-1900 mean
    baseline_mask = (scenario_temp['Year'] >= 1850) & (scenario_temp['Year'] <= 1901)
    baseline_mean = scenario_temp[baseline_mask]['Temperature_median'].mean()
    
    temp_median = scenario_temp['Temperature_median'].values - baseline_mean
    temp_p05 = scenario_temp['Temperature_p05'].values - baseline_mean
    temp_p95 = scenario_temp['Temperature_p95'].values - baseline_mean
    
    # Plot uncertainty band (using p05/p95 as approximation for p33/p66)
    ax[1].fill_between(
        years,
        temp_p05,
        temp_p95, 
        color=meta[2],
        lw=0,
        alpha=0.3,
        label=scenario,
    )

# Add historical overlay (black shading up to 2023)
hist_scenario = temp_df[temp_df['Scenario'] == list(scenario_model_match.keys())[0]]
hist_mask = hist_scenario['Year'] <= cfg.future_start_year
hist_years = hist_scenario[hist_mask]['Year'].values
baseline_mask = (hist_scenario['Year'] >= 1850) & (hist_scenario['Year'] <= cfg.historical_start_year + 1)
baseline_mean = hist_scenario[baseline_mask]['Temperature_median'].mean()
hist_p05 = (hist_scenario[hist_mask]['Temperature_p05'].values - baseline_mean)
hist_p95 = (hist_scenario[hist_mask]['Temperature_p95'].values - baseline_mean)

ax[1].fill_between(
    hist_years,
    hist_p05,
    hist_p95,
    color="k",
    alpha=0.5,
)

ax[1].axhline(0, ls=":", color="k", lw=0.5)
ax[1].set_ylabel("Temperature above 1850-1900, K")
ax[1].set_ylim(0, 5)
ax[1].set_xlim(2000, 2150)
ax[1].grid()
ax[1].legend()
ax[1].set_title("(b)")

pl.tight_layout()
pl.savefig(PLOTS_DIR / "temperature_emis.png", dpi=600, bbox_inches='tight')
pl.savefig(PLOTS_DIR / "temperature_emis.pdf", format='pdf', bbox_inches='tight')
print("✓ Saved: temperature_emis.png and temperature_emis.pdf")

# %% [markdown]
# ## Plot 2: Extensions Diagnostics (extensions.png)
#
# 8-panel diagnostic plot showing:
# - CO2 FFI emissions
# - CO2 AFOLU emissions  
# - CH4 emissions
# - Cumulative CO2 emissions
# - Sulfur emissions
# - Total CO2e emissions
# - Total forcing
# - CO2 concentration
# - Temperature anomaly

# %%
fig, ax = pl.subplots(4, 2, figsize=(8, 12))

# Panel 0: CO2 FFI emissions
for scenario, meta in scenario_model_match.items():
    scenario_data = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'CO2 FFI')
    ]
    ax[0, 0].plot(
        scenario_data['Year'],
        scenario_data['Emissions'].values / 1e6,
        color=meta[2],
        label=scenario
    )
ax[0, 0].set_ylabel("CO$_2$ FFI emissions,\\nGtCO$_2$ yr$^{-1}$")
ax[0, 0].set_xlim(1750, 2500)
ax[0, 0].axhline(0, color='k', lw=0.5, ls=':')
ax[0, 0].grid()
ax[0, 0].legend(fontsize=8)

# Panel 1: CO2 AFOLU emissions  
for scenario, meta in scenario_model_match.items():
    scenario_data = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'CO2 AFOLU')
    ]
    ax[0, 1].plot(
        scenario_data['Year'],
        scenario_data['Emissions'].values / 1e6,
        color=meta[2]
    )
ax[0, 1].set_ylabel("CO$_2$ AFOLU emissions,\\nGtCO$_2$ yr$^{-1}$")
ax[0, 1].set_xlim(1750, 2500)
ax[0, 1].axhline(0, color='k', lw=0.5, ls=':')
ax[0, 1].grid()

# Panel 2: CH4 emissions
for scenario, meta in scenario_model_match.items():
    scenario_data = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'CH4')
    ]
    ax[1, 0].plot(
        scenario_data['Year'],
        scenario_data['Emissions'].values,
        color=meta[2]
    )
ax[1, 0].set_ylabel("CH$_4$ emissions,\\nMtCH$_4$ yr$^{-1}$")
ax[1, 0].set_xlim(1750, cfg.extensions_end_year)
ax[1, 0].axhline(0, color='k', lw=0.5, ls=':')
ax[1, 0].grid()

# Panel 3: Cumulative CO2 emissions (calculate from CO2 FFI + AFOLU)
for scenario, meta in scenario_model_match.items():
    co2_ffi = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'CO2 FFI')
    ].set_index('Year')['Emissions']
    
    co2_afolu = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'CO2 AFOLU')
    ].set_index('Year')['Emissions']
    
    cumulative = (co2_ffi + co2_afolu).cumsum() / 1e6
    ax[1, 1].plot(
        cumulative.index,
        cumulative.values,
        color=meta[2]
    )
ax[1, 1].set_ylabel("Cumulative CO$_2$,\\nGtCO$_2$")
ax[1, 1].set_xlim(1750, 2500)
ax[1, 1].axhline(0, color='k', lw=0.5, ls=':')
ax[1, 1].grid()

# Panel 4: Sulfur emissions
for scenario, meta in scenario_model_match.items():
    scenario_data = emis_species_df[
        (emis_species_df['Scenario'] == scenario) & 
        (emis_species_df['Species'] == 'Sulfur')
    ]
    ax[2, 0].plot(
        scenario_data['Year'],
        scenario_data['Emissions'].values,
        color=meta[2]
    )
ax[2, 0].set_ylabel("Sulfur emissions,\\nMtS yr$^{-1}$")
ax[2, 0].set_xlim(1750, cfg.extensions_end_year)
ax[2, 0].axhline(0, color='k', lw=0.5, ls=':')
ax[2, 0].grid()

# Panel 5: Total CO2e emissions
for scenario, meta in scenario_model_match.items():
    scenario_data = co2e_df[co2e_df['Scenario'] == scenario]
    ax[2, 1].plot(
        scenario_data['Year'],
        scenario_data['CO2e_emissions'].values / 1e6,
        color=meta[2]
    )
ax[2, 1].set_ylabel("Total CO$_2$e emissions,\\nGtCO$_2$eq yr$^{-1}$")
ax[2, 1].set_xlim(1750, cfg.extensions_end_year)
ax[2, 1].axhline(0, color='k', lw=0.5, ls=':')
ax[2, 1].grid()

# Panel 6: Total forcing
for scenario, meta in scenario_model_match.items():
    scenario_data = forcing_sum_df[forcing_sum_df['Scenario'] == scenario]
    years = scenario_data['Year'].values
    forcing_median = scenario_data['Forcing_sum_median'].values
    forcing_p05 = scenario_data['Forcing_sum_p05'].values
    forcing_p95 = scenario_data['Forcing_sum_p95'].values
    
    ax[3, 0].fill_between(
        years,
        forcing_p05,
        forcing_p95,
        color=meta[2],
        alpha=0.3,
        lw=0
    )
    ax[3, 0].plot(years, forcing_median, color=meta[2])

ax[3, 0].set_ylabel("Total forcing,\\nW m$^{-2}$")
ax[3, 0].set_xlabel("Year")
ax[3, 0].set_xlim(1750, cfg.extensions_end_year)
ax[3, 0].axhline(0, color='k', lw=0.5, ls=':')
ax[3, 0].grid()

# Panel 7: Temperature anomaly
for scenario, meta in scenario_model_match.items():
    scenario_data = temp_df[temp_df['Scenario'] == scenario]
    years = scenario_data['Year'].values
    
    # Calculate anomaly relative to 1850-1900
    baseline_mask = (scenario_data['Year'] >= 1850) & (scenario_data['Year'] <= 1901)
    baseline_mean = scenario_data[baseline_mask]['Temperature_median'].mean()
    
    temp_median = scenario_data['Temperature_median'].values - baseline_mean
    temp_p05 = scenario_data['Temperature_p05'].values - baseline_mean
    temp_p95 = scenario_data['Temperature_p95'].values - baseline_mean
    
    ax[3, 1].fill_between(
        years,
        temp_p05,
        temp_p95,
        color=meta[2],
        alpha=0.3,
        lw=0
    )
    ax[3, 1].plot(years, temp_median, color=meta[2])

ax[3, 1].set_ylabel("Temperature anomaly,\\nK above 1850-1900")
ax[3, 1].set_xlabel("Year")
ax[3, 1].set_xlim(1750, 2500)
ax[3, 1].axhline(0, color='k', lw=0.5, ls=':')
ax[3, 1].grid()

pl.tight_layout()
pl.savefig(PLOTS_DIR / "extensions.png", dpi=600, bbox_inches='tight')
pl.savefig(PLOTS_DIR / "extensions.pdf", format='pdf', bbox_inches='tight')
print("✓ Saved: extensions.png and extensions.pdf")

# %% [markdown]
# ## Plot 3: Temperature Probability Distributions (ECDF)
#
# Three-panel plot showing empirical cumulative distribution functions (ECDFs) for:
# - Temperature at 2100 relative to 1850-1900
# - Temperature at 2300 relative to 1850-1900
# - Maximum temperature excursion relative to 1850-1900

# %%
fig, ax = pl.subplots(1, 3, figsize=(15, 4))

column_names = ['Temp_2100_anomaly', 'Temp_2300_anomaly', 'Temp_max_anomaly']
titles = ['2100', '2300', 'Maximum']
panels = ['(a)', '(b)', '(c)']

for panel_idx, (column, title, panel_label) in enumerate(zip(column_names, titles, panels)):
    for scenario, meta in scenario_model_match.items():
        # Get all ensemble member values for this scenario and metric
        scenario_data = ecdf_df[ecdf_df['Scenario'] == scenario]
        
        # Sort values to create ECDF
        values = np.sort(scenario_data[column].values)
        
        # Calculate cumulative probabilities (0 to 1)
        n = len(values)
        probabilities = np.arange(1, n + 1) / n
        
        # Plot ECDF
        ax[panel_idx].plot(
            values,
            probabilities * 100,  # Convert to percentage
            color=meta[2],
            label=scenario if panel_idx == 2 else None,  # Legend only on last panel
            lw=1.5
        )
    
    ax[panel_idx].set_xlabel(f"Temperature in {title},\\nK above 1850-1900")
    ax[panel_idx].set_ylabel("Cumulative probability, %")
    ax[panel_idx].set_ylim(0, 100)
    ax[panel_idx].grid(alpha=0.3)
    ax[panel_idx].set_title(panel_label)
    
    # Add reference lines for key percentiles
    ax[panel_idx].axhline(50, color='gray', ls='--', lw=0.5, alpha=0.5)
    ax[panel_idx].axhline(5, color='gray', ls=':', lw=0.5, alpha=0.5)
    ax[panel_idx].axhline(95, color='gray', ls=':', lw=0.5, alpha=0.5)

# Add legend to rightmost panel
ax[2].legend(loc='lower right', fontsize=9)

pl.tight_layout()
pl.savefig(PLOTS_DIR / "temperature_ecdf.png", dpi=600, bbox_inches='tight')
pl.savefig(PLOTS_DIR / "temperature_ecdf.pdf", format='pdf', bbox_inches='tight')
print("✓ Saved: temperature_ecdf.png and temperature_ecdf.pdf")
