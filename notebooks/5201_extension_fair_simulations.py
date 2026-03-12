# %% [markdown]
# # FaIR Climate Model Simulations with Extended Emissions Scenarios
#
# This notebook runs the FaIR v2.2 climate model with extended emissions scenarios (1750-2501)
# to generate climate projections. It processes emissions through CO2-equivalent calculations,
# applies blending for smooth transitions, and produces temperature and concentration projections
# across seven scenarios ranging from very low (VL) to very high (HL) emissions.

# %%
import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as pl
import numpy as np
import pandas as pd
import pooch
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties

# %%
f = FAIR()
memory_limited = True

# %% [markdown]
#

# %%
snames = ["VL", "LN", "L", "ML", "M", "H", "HL"]
snames_short = ["VL", "LN", "L", "ML", "M", "H", "HL"]
sname21_short = ["VL", "LN", "L", "ML", "M", "H", "HL"]

f.define_time(1750, 2501, 1)
f.define_scenarios(snames)
species, properties = read_properties("../data/fair-inputs/species_configs_properties_1.4.1.csv")
f.define_species(species, properties)
f.ch4_method = "Thornhill2021"


# %% [markdown]
# 'memory_limited' is for testing, runs only 5 ensemble members.
#
# If running full AR6 ensemble, need to
# - set 'memory_limited' to False
# - config file will be pulled from zenodo
#

# %%
if ~memory_limited:
    # Define the Zenodo record DOI and the specific file you want
    ZENODO_DOI = "10.5281/zenodo.7112539"  # Replace with your Zenodo DOI
    FILE_NAME = "calibrated_constrained_parameters.csv"  # Replace with your file name on Zenodo
    FILE_HASH = "md5:8a70a3fb05d0e0cf35e136de382582a5"  # Replace with the actual SHA256 hash of your file

    # Create a Pooch instance
    data_pooch = pooch.create(
        path="../data/fair-inputs",  # Local cache directory
        base_url=f"doi:{ZENODO_DOI}",  # Zenodo DOI as base URL
        version="1.5.0",
        registry={FILE_NAME: FILE_HASH},
    )

    # Fetch the file
    local_file_path = data_pooch.fetch(FILE_NAME)

    print(f"Config file downloaded to: {local_file_path}")

# %%
if memory_limited:
    df_configs = pd.read_csv("../data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv", index_col=0)
    f.define_configs(df_configs.index)
else:
    df_configs = pd.read_csv("../data/fair-inputs/1.5.0/calibrated_constrained_parameters.csv", index_col=0)
    f.define_configs(df_configs.index)

# %%
f.allocate()

# %%
scens = f.emissions.scenario.values

# %%
ldict = {}
ldict21 = {}
for i, s in enumerate(snames):
    ldict[s] = snames_short[i]
    ldict21[s] = sname21_short[i]


# %% [markdown]
# ../data/fair-inputs/emissions_1750-2500.csv
# is generated from 0503_extension_functioality_as_notebook.py

# %%
df_emis = pd.read_csv("../outputs/continuous_emissions_timeseries_1750_2500.csv")
df_emis.head()

# %% [markdown]
# ## Setup and Configuration
#
# **Scenarios**: Seven emissions scenarios (VL, LN, L, ML, M, H, HL) representing very low
# to very high emissions pathways
# **Time range**: 1750-2501 (752 years)
# **Species**: CO2 (FFI & AFOLU), CH4, N2O, plus 37 other GHGs and aerosols
# **FaIR configuration**: Using calibrated parameters from Smith et al. with legacy CH4 lifetime method

# %%
gwpmat = pd.read_csv("../data/fair-inputs/gwp_mass_adjusted_100y.csv", index_col=0)

# %%
f.fill_from_csv(
    forcing_file="../data/fair-inputs/volcanic_solar.csv",
    emissions_file="../data/fair-inputs/emissions_1750-2500.csv",
)

# %%
gwp_nonco2 = gwpmat.copy()
gwp_nonco2.loc["CO2 AFOLU"] = np.nan
gwp_nonco2.loc["CO2 FFI"] = np.nan


# %%
nonco2 = f.emissions.sel(specie="CO2 FFI")[:, :, 0].copy()
for specie in f.emissions.specie.values:
    try:
        gwp = gwp_nonco2[specie]
    except KeyError:
        gwp = np.nan
    if ~np.isnan(gwp):
        nonco2 = nonco2 + f.emissions.sel(specie=specie)[:, :, 0] * gwp
    else:
        0


# %%
ncflr = np.ones(len(scens))
for i in range(len(scens)):
    ncflr[i] = nonco2.sel(scenario=scens[i])[-1] / 1e6
ncflr

# %%
scens_shrt = [ldict[s] for s in scens]

# %% [markdown]
# ## CO2-Equivalent Emissions Calculation
#
# Convert all GHG emissions to CO2-equivalents using 100-year Global Warming Potentials (GWP100).
# This aggregates the climate forcing from all greenhouse gases into a single metric for
# comparison across scenarios.
#
# **Method**: Multiply each species' emissions by its GWP (e.g., CH4 = 29.8, N2O = 273) and sum to get total CO2e.

# %% [markdown]
#
# - Solar forcing set to zero (natural forcing handled separately by FaIR)

# %%
for s in f.scenarios:
    f.forcing.loc[dict(scenario=s, specie="Solar")] = 0


# %%
scens_out = []
for s in scens:
    df_scen = f.emissions.sel(scenario=s, config=df_configs.index[0]).to_pandas().T
    df_scen.insert(loc=0, column="Scenario", value=s)
    df_scen.dropna(inplace=True)
    scens_out.append(df_scen)
scens_out = pd.concat(scens_out)


# %% [markdown]
# Calculate CO2e

# %%
co2eo = f.emissions.sel(specie="CO2 FFI")[:, :, 0].copy() * 0
for specie in f.emissions.specie.values:
    try:
        gwp = gwpmat["ar6_gwp_mass_adjusted"][specie]

    except KeyError:
        gwp = np.nan
    if ~np.isnan(gwp):
        co2eo = co2eo + f.emissions.sel(specie=specie)[:, :, 0] * gwp / 1000000
    else:
        0
co2e = co2eo * 1e6  # -co2eo.loc[dict(timepoints=2019.5)].values+53.e6

# %% [markdown]
# ## Run FaIR

# %%
f.fill_species_configs("../data/fair-inputs/species_configs_properties_1.4.1.csv")
if memory_limited:
    f.override_defaults("../data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv")
else:
    f.override_defaults("../data/fair-inputs/1.5.0/calibrated_constrained_parameters.csv")
initialise(f.concentration, f.species_configs["baseline_concentration"])
initialise(f.forcing, 0)
initialise(f.temperature, 0)
initialise(f.cumulative_emissions, 0)
initialise(f.airborne_emissions, 0)
initialise(f.ocean_heat_content_change, 0)
f.run()

# %% [markdown]
# ## Export Climate Model Outputs
#
# Save FaIR model outputs to CSV for visualization in separate notebook:
# - Temperature: median and quantiles (5th, 95th percentiles) by scenario
# - Forcing: median by species and scenario
# - Concentration: median for key GHGs (CO2, CH4, N2O) by scenario
# - Emissions: preprocessed inputs used by FaIR

# %%
# Suppress All-NaN slice warnings during export
# (These occur when forcing species have no data for certain scenarios/configs)
import warnings
warnings.filterwarnings('ignore', message='All-NaN slice encountered')

# %%
# Export temperature summary statistics
print("Exporting temperature data...")
temp_df_list = []
for scenario in f.scenarios:
    temp_data = f.temperature.sel(scenario=scenario, layer=0)
    df_temp = pd.DataFrame({
        'Scenario': scenario,
        'Year': f.timebounds,
        'Temperature_median': temp_data.median(dim='config').values,
        'Temperature_p05': temp_data.quantile(0.05, dim='config').values,
        'Temperature_p95': temp_data.quantile(0.95, dim='config').values,
    })
    temp_df_list.append(df_temp)

temp_summary = pd.concat(temp_df_list, ignore_index=True)
temp_summary.to_csv('../outputs/fair_temperature_1750-2500.csv', index=False)
print(f"  Saved temperature data: {len(temp_summary)} rows")

# Export forcing by species (median only to keep file size manageable)
print("Exporting forcing data...")
forcing_df_list = []
for scenario in f.scenarios:
    for species in f.forcing.specie.values:
        forcing_data = f.forcing.sel(scenario=scenario, specie=species)
        df_forcing = pd.DataFrame({
            'Scenario': scenario,
            'Species': species,
            'Year': f.timebounds,
            'Forcing_median': forcing_data.median(dim='config').values,
            'Forcing_p05': forcing_data.quantile(0.05, dim='config').values,
            'Forcing_p95': forcing_data.quantile(0.95, dim='config').values,
        })
        forcing_df_list.append(df_forcing)

forcing_summary = pd.concat(forcing_df_list, ignore_index=True)
forcing_summary.to_csv('../outputs/fair_forcing_1750-2500.csv', index=False)
print(f"  Saved forcing data: {len(forcing_summary)} rows")

# Export key GHG concentrations (CO2, CH4, N2O)
print("Exporting concentration data...")
key_species = ['CO2', 'CH4', 'N2O']
conc_df_list = []
for scenario in f.scenarios:
    for species in key_species:
        conc_data = f.concentration.sel(scenario=scenario, specie=species)
        df_conc = pd.DataFrame({
            'Scenario': scenario,
            'Species': species,
            'Year': f.timebounds,
            'Concentration_median': conc_data.median(dim='config').values,
            'Concentration_p05': conc_data.quantile(0.05, dim='config').values,
            'Concentration_p95': conc_data.quantile(0.95, dim='config').values,
        })
        conc_df_list.append(df_conc)

conc_summary = pd.concat(conc_df_list, ignore_index=True)
conc_summary.to_csv('../outputs/fair_concentration_ghgs_1750-2500.csv', index=False)
print(f"  Saved concentration data: {len(conc_summary)} rows")

# Export CO2e emissions (already calculated earlier)
print("Exporting CO2e emissions...")
co2e_df_list = []
for scenario in f.scenarios:
    df_co2e = pd.DataFrame({
        'Scenario': scenario,
        'Year': f.timepoints,
        'CO2e_emissions': co2e.sel(scenario=scenario).values,
    })
    co2e_df_list.append(df_co2e)

co2e_summary = pd.concat(co2e_df_list, ignore_index=True)
co2e_summary.to_csv('../outputs/fair_co2e_emissions_1750-2500.csv', index=False)
print(f"  Saved CO2e emissions: {len(co2e_summary)} rows")

# %%
# Export full ensemble data for ECDF plots (specific years only)
print("Exporting ensemble data for ECDF plots...")
ecdf_df_list = []

for scenario in f.scenarios:
    temp_data = f.temperature.sel(scenario=scenario, layer=0)
    
    # Get temperature at specific years for each ensemble member
    for config_idx, config in enumerate(f.configs):
        temp_2100 = temp_data.sel(config=config, timebounds=2100).values
        temp_2300 = temp_data.sel(config=config, timebounds=2300).values
        temp_1850 = temp_data.sel(config=config, timebounds=1850).values
        temp_max = temp_data.sel(config=config).max(dim='timebounds').values
        
        df_ecdf = pd.DataFrame({
            'Scenario': [scenario],
            'Config': [config],
            'Temp_2100_anomaly': [temp_2100 - temp_1850],
            'Temp_2300_anomaly': [temp_2300 - temp_1850],
            'Temp_max_anomaly': [temp_max - temp_1850],
        })
        ecdf_df_list.append(df_ecdf)

ecdf_data = pd.concat(ecdf_df_list, ignore_index=True)
ecdf_data.to_csv('../outputs/fair_temperature_ecdf_data.csv', index=False)
print(f"  Saved ECDF data: {len(ecdf_data)} rows ({len(f.configs)} configs × {len(f.scenarios)} scenarios)")
print(f"  File size estimate: ~{len(ecdf_data) * 80 / 1024:.1f} KB")

# %%
# Export emissions by species (first config for diagnostic plots)
print("Exporting emissions by species...")
emissions_species = ['CO2 FFI', 'CO2 AFOLU', 'CH4', 'Sulfur']
emis_species_list = []

for scenario in f.scenarios:
    for species in emissions_species:
        df_species = pd.DataFrame({
            'Scenario': scenario,
            'Species': species,
            'Year': f.timepoints,
            'Emissions': f.emissions.sel(scenario=scenario, specie=species, config=f.configs[0]).values,
        })
        emis_species_list.append(df_species)

emis_species_df = pd.concat(emis_species_list, ignore_index=True)
emis_species_df.to_csv('../outputs/fair_emissions_by_species.csv', index=False)
print(f"  Saved species emissions: {len(emis_species_df)} rows")

# Export total forcing (forcing_sum)
print("Exporting total forcing...")
forcing_sum_list = []

for scenario in f.scenarios:
    df_forcing_sum = pd.DataFrame({
        'Scenario': scenario,
        'Year': f.timebounds,
        'Forcing_sum_median': f.forcing_sum.sel(scenario=scenario).median(dim='config').values,
        'Forcing_sum_p05': f.forcing_sum.sel(scenario=scenario).quantile(0.05, dim='config').values,
        'Forcing_sum_p95': f.forcing_sum.sel(scenario=scenario).quantile(0.95, dim='config').values,
    })
    forcing_sum_list.append(df_forcing_sum)

forcing_sum_df = pd.concat(forcing_sum_list, ignore_index=True)
forcing_sum_df.to_csv('../outputs/fair_forcing_sum_1750-2500.csv', index=False)
print(f"  Saved total forcing: {len(forcing_sum_df)} rows")

# %%
print("\n" + "="*60)
print("All climate model outputs saved to outputs/ directory:")
print("  - fair_temperature_1750-2500.csv (summary statistics)")
print("  - fair_forcing_1750-2500.csv (by species)")
print("  - fair_concentration_ghgs_1750-2500.csv (CO2, CH4, N2O)")
print("  - fair_co2e_emissions_1750-2500.csv")
print("  - fair_temperature_ecdf_data.csv (for probability plots)")
print("  - fair_emissions_by_species.csv")
print("  - fair_forcing_sum_1750-2500.csv (total ERF)")
print("="*60)

