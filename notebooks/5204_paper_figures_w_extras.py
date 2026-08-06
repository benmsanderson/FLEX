# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: default
#     language: python
#     name: python3
# ---

# %% [markdown]
#
#
# # Presentation Figures
#
# Generates all data-driven figures for `docs/scenariomip_overview.md`.
#
# **Inputs:**
# - `outputs/scenariomip_default/` — FaIR outputs and extended emissions
# - `outputs/WIEMIP/` — counterfactual FaIR outputs
# - `data/scenarios_regional.csv` — pre-2100 IAM regional data (CDR tech, R5)
# - `docs/ssp2_com/` — SSP2-com global emissions
#
# **Outputs:** `outputs/presentation/figXX_name.png` (300 dpi)

# %% tags=["parameters"]
config_name = "scenariomip_default"
wiemip_config = "WIEMIP"

# %% [markdown]
# ## Setup

# %%
# %matplotlib inline
import warnings
import glob
import os
import sys
from pathlib import Path

import matplotlib.pyplot as pl
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from flex.config import load_config, DATA_DIR

warnings.filterwarnings("ignore", message="All-NaN slice encountered")

cfg = load_config(config_name)
wcfg = load_config(wiemip_config)
print(DATA_DIR)
#sys.exit(4)

OUTPUTS_DIR = cfg.outputs_dir
WIEMIP_DIR = wcfg.outputs_dir
PROJECT_ROOT = DATA_DIR.parent
SSP2COM_DIR = PROJECT_ROOT / "docs" / "ssp2_com"
PLOTS_DIR = PROJECT_ROOT / "outputs" / "presentation"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Scenariomip outputs: {OUTPUTS_DIR}")
print(f"WIEMIP outputs:      {WIEMIP_DIR}")
print(f"SSP2-com data:       {SSP2COM_DIR}")
print(f"Saving figures to:   {PLOTS_DIR}")


# %%
# --- Scenario colour map and display names ---
_smm_raw = cfg.scenario_model_match  # {label: [scenario, model, color]}
# Normalise to dict-of-dicts for uniform access
SCENARIO_META = {k: {"scenario": v[0], "model": v[1], "color": v[2]} for k, v in _smm_raw.items()}
SCEN_COLOR = {k: v["color"] for k, v in SCENARIO_META.items()}
SCEN_LABELS = list(SCENARIO_META.keys())

# Colour overrides for better contrast on white
SCEN_COLOR["LN"] = "#0097a0"
SCEN_COLOR["ML"] = "#907000"
SCEN_COLOR["HL"] = "#8a10a8"

COM_COLOR = "#555555"   # SSP2-com
HIST_COLOR = "#222222"  # Historical

# %%
# --- Global matplotlib style ---
pl.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 11,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

PARIS_15 = 1.5
PARIS_20 = 2.0
HIST_END = 2023    # year historical period ends
EXT_START = 2100   # year extension begins

def add_paris_lines(ax, xlim=None):
    """Add 1.5°C and 2°C reference lines to a temperature axis."""
    kw = dict(color="#888", lw=0.8, ls="--", zorder=0)
    ax.axhline(PARIS_15, **kw)
    ax.axhline(PARIS_20, **kw)
    if xlim:
        ax.text(xlim[1] + 1, PARIS_15, "1.5°C", va="center", fontsize=8, color="#888")
        ax.text(xlim[1] + 1, PARIS_20, "2.0°C", va="center", fontsize=8, color="#888")

def save(fig, name):
    path = PLOTS_DIR / name
    fig.savefig(path)
    print(f"  Saved {path.name}")
    #pl.show()
    pl.close(fig)
print(OUTPUTS_DIR)
#sys.exit(4)

# %% [markdown]
# ## A — Load scenariomip_default outputs

# %%
temp_df     = pd.read_csv(OUTPUTS_DIR / "fair_temperature_1750-2500.csv")
emis_df     = pd.read_csv(OUTPUTS_DIR / "fair_emissions_by_species.csv")
co2e_df     = pd.read_csv(OUTPUTS_DIR / "fair_co2e_emissions_1750-2500.csv")
ecdf_df     = pd.read_csv(OUTPUTS_DIR / "fair_temperature_ecdf_data.csv")
forcing_df  = pd.read_csv(OUTPUTS_DIR / "fair_forcing_sum_1750-2500.csv")
forcing_persp_df  = pd.read_csv(OUTPUTS_DIR / "fair_forcing_1750-2500.csv")
conc_df     = pd.read_csv(OUTPUTS_DIR / "fair_concentration_ghgs_1750-2500.csv")
cont_df     = pd.read_csv(OUTPUTS_DIR / "continuous_emissions_timeseries_1750_2500.csv")

print(emis_df["Species"].unique())
#sys.exit(4)
# Compute temperature anomaly relative to 1850-1900 for each scenario
def baseline_mean(df, scenario):
    mask = (df["Scenario"] == scenario) & (df["Year"] >= 1850) & (df["Year"] <= 1900)
    return df.loc[mask, "Temperature_median"].mean()

BASELINE = {s: baseline_mean(temp_df, s) for s in SCEN_LABELS}
print("Baselines (1850-1900 mean temp):")
for k, v in BASELINE.items():
    print(f"  {k}: {v:.4f} K")

# %%
# Helper: get scenario temperature anomaly
def temp_anom(scenario):
    d = temp_df[temp_df["Scenario"] == scenario].copy()
    bl = BASELINE[scenario]
    d["T_med"] = d["Temperature_median"] - bl
    d["T_p05"] = d["Temperature_p05"] - bl
    d["T_p95"] = d["Temperature_p95"] - bl
    return d

# Helper: get species emissions for one scenario
def get_emis(scenario, species, dataframe=emis_df):
    return dataframe[(dataframe["Scenario"] == scenario) & (dataframe["Species"] == species)]

# Helper: get variable from continuous timeseries
def get_cont(scenario, variable):
    scen_name = SCENARIO_META[scenario]["scenario"]
    mask = (cont_df["scenario"] == scen_name) & (cont_df["variable"] == variable)
    d = cont_df[mask].copy()
    year_cols = [c for c in d.columns if isinstance(c, float) or (isinstance(c, str) and c.replace(".", "").isdigit())]
    if not year_cols:
        year_cols = [c for c in d.columns if c not in ["model","scenario","region","workflow","variable","unit"]]
    vals = d[year_cols].values.flatten()
    years = np.array([float(y) for y in year_cols])
    return years, vals




# %%
import pooch
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties

params_file = DATA_DIR / "fair-inputs" / "1.6.0" / "calibrated_constrained_parameters.csv"
species_file = str(DATA_DIR / "fair-inputs" / "species_configs_properties_1.4.1.csv")
forcing_file = str(DATA_DIR / "fair-inputs" / "volcanic_solar.csv")
emis_file    = str(OUTPUTS_DIR / "emissions_1750-2500.csv")  # use ML as template


# %% [markdown]
# ## D — CDR technology breakdown (pre-2100 from IAM data)

# %%
# Load IAM regional data to extract CDR technology breakdown
# Variables: Emissions|CO2|BECCS, |Direct Air Capture, |Ocean, |Enhanced Weathering, |Biochar, |Soil Carbon Management
CDR_VARS = {
    "BECCS":               "Emissions|CO2|BECCS",
    "DACCS":               "Emissions|CO2|Direct Air Capture",
    "Ocean CDR":           "Emissions|CO2|Ocean",
    "Enhanced Weathering": "Emissions|CO2|Enhanced Weathering",
    "Biochar":             "Emissions|CO2|Biochar",
    "Soil Carbon":         "Emissions|CO2|Soil Carbon Management",
}

print("Loading scenarios_regional.csv …")
scen_reg = pd.read_csv(DATA_DIR / "scenarios_regional.csv")
print(f"  shape: {scen_reg.shape}")
avail_vars = scen_reg["variable"].unique()
cdr_avail = {k: v for k, v in CDR_VARS.items() if v in avail_vars}
print(f"  CDR vars found: {list(cdr_avail.keys())}")
#sys.exit(4)

# %%
# For each scenario and each CDR tech, extract world total at 5-year intervals
def get_cdr_tech(scen_label, tech_var):
    """Return (years, values) for a CDR technology in a given scenario."""
    scen_name = SCENARIO_META[scen_label]["scenario"]
    mask = (scen_reg["scenario"] == scen_name) & (scen_reg["variable"] == tech_var) & (scen_reg["region"] == "World")
    row = scen_reg[mask]
    if row.empty:
        return None, None
    year_cols = [c for c in row.columns if str(c).isdigit()]
    years = np.array([int(c) for c in year_cols])
    vals  = row[year_cols].values.flatten().astype(float)
    return years, vals

# Compute CDR tech fractions at 2100 for each scenario, then project post-2100
CDR_DATA = {}   # {scenario: DataFrame with columns Year, tech1, tech2, …}

for scen in SCEN_LABELS:
    rows = []
    tech_names_found = []
    for tech_name, tech_var in cdr_avail.items():
        yy, vv = get_cdr_tech(scen, tech_var)
        if yy is None:
            continue
        tech_names_found.append(tech_name)
        # Interpolate to annual 2023-2100
        cs_tech = CubicSpline(yy, vv, extrapolate=True)
        ann_years = np.arange(2023, 2101)
        ann_vals  = np.maximum(0, cs_tech(ann_years))  # CDR is negative; clamp positive to 0
        rows.append(pd.Series(ann_vals, index=ann_years, name=tech_name))

    if rows:
        df_cdr = pd.DataFrame(rows).T
        df_cdr.index.name = "Year"

        # Post-2100: scale each tech by the gross removals extension trajectory
        # Get 2100 total from CDR dataframe
        total_2100 = df_cdr.loc[2100].sum()
        if total_2100 != 0:
            fracs_2100 = df_cdr.loc[2100] / total_2100
        else:
            fracs_2100 = pd.Series(1.0 / len(tech_names_found), index=tech_names_found)

        # Get gross removals from continuous timeseries (post-2100)
        scen_name = SCENARIO_META[scen]["scenario"]
        gr_mask = (cont_df["scenario"] == scen_name) & (cont_df["variable"] == "Emissions|CO2|Gross Removals")
        gr_row = cont_df[gr_mask]
        if not gr_row.empty:
            year_cols = [c for c in gr_row.columns if str(c).replace(".","").isdigit()]
            gr_years = np.array([float(c) for c in year_cols])
            gr_vals  = gr_row[year_cols].values.flatten().astype(float)
            # post-2100 extension years
            ext_mask = gr_years > 2100
            ext_years = gr_years[ext_mask].astype(int)
            ext_total = gr_vals[ext_mask]
            # Build post-2100 rows
            ext_rows = {}
            for tech in tech_names_found:
                ext_rows[tech] = fracs_2100[tech] * ext_total
            df_ext = pd.DataFrame(ext_rows, index=ext_years)
            df_ext.index.name = "Year"
            df_cdr = pd.concat([df_cdr, df_ext])

        CDR_DATA[scen] = df_cdr

if CDR_DATA:
    print("CDR tech data available for:", list(CDR_DATA.keys()))
    print("  Technologies:", list(list(CDR_DATA.values())[0].columns))
else:
    print("No CDR technology breakdown available — will show aggregate only.")

# %% [markdown]
# ## E — R5 regional disaggregation

# %%
R5_MAP = {
    "OECD90": ["United States", "EU 28", "Japan", "Canada, Australia", "Non-EU28 Europe"],
    "REF":    ["Russia"],
    "ASIA":   ["China", "India", "Other Asia"],
    "MAF":    ["Middle East", "Sub-Saharan Africa", "North Africa"],
    "LAM":    ["Latin America"],
}
R5_COLORS = {
    "OECD90": "#2166ac",
    "REF":    "#762a83",
    "ASIA":   "#d6604d",
    "MAF":    "#f4a582",
    "LAM":    "#4dac26",
}

def classify_r5(region_str):
    """Map a model|region string to one of the R5 categories."""
    r = region_str.split("|", 1)[-1] if "|" in region_str else region_str
    for r5, keywords in R5_MAP.items():
        if any(kw.lower() in r.lower() for kw in keywords):
            return r5
    return None   # World or unknown

def get_r5_emissions(scen_label, variable="Emissions|CO2|Energy and Industrial Processes"):
    """
    Return a dict {R5_region: (years, values)} for a given scenario and variable,
    read from the per-model extension file.
    """
    model_name = SCENARIO_META[scen_label]["model"].replace(" ", "_").replace("/", "_").replace(",", "")
    # Try to find the extension file
    candidates = list((OUTPUTS_DIR).glob(f"extensions_{model_name}*.csv"))
    #print(candidates)

    if not candidates:
        # Try partial match
        candidates = list(OUTPUTS_DIR.glob("extensions_*.csv"))
        candidates = [c for c in candidates if scen_label in c.stem or
                      SCENARIO_META[scen_label]["model"].split()[0] in c.stem]
    if not candidates:
        print(f"  No extension file found for {scen_label}")
        return {}

    df_ext = pd.read_csv(candidates[0])
    #print(df_ext["variable"].unique())

    var_mask = df_ext["variable"] == variable
    result = {}
    for r5 in R5_MAP:
        r5_total = None
        for _, row in df_ext[var_mask].iterrows():
            region = row["region"]
            #print(region)
            if classify_r5(region) == r5:
                year_cols = [c for c in df_ext.columns if str(c).replace(".","").isdigit()]
                years = np.array([float(c) for c in year_cols])
                vals  = row[year_cols].values.astype(float)
                if r5_total is None:
                    r5_total = (years, vals.copy())
                else:
                    r5_total = (r5_total[0], r5_total[1] + vals)
        if r5_total is not None:
            result[r5] = r5_total   
    return result

# Test
r5_vl = get_r5_emissions("VL")

print("R5 regions found for VL:", list(r5_vl.keys()))

for scen_label in SCENARIO_META.keys():
    r5_regs = get_r5_emissions(scen_label)

    print(f"R5 regions found for {scen_label}:", list(r5_regs.keys()))

# %% [markdown]
# ## Section 3 figures — ScenarioMIP to 2100

# %% [markdown]
# ### F01 — VL narrative: CO₂ components + temperature (2020–2100)

# %%
fig, axes = pl.subplots(1, 2, figsize=(10, 4))

scen = "VL"
color = SCEN_COLOR[scen]

# Panel 0: Net CO2 (FFI + AFOLU)
d_ffi = get_emis(scen, "CO2 FFI")
d_afolu = get_emis(scen, "CO2 AFOLU")
net = (d_ffi["Emissions"].values + d_afolu["Emissions"].values) / 1e6
ax = axes[0]
ax.plot(d_ffi["Year"], net, color=color, lw=2)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(2020, 2500)
ax.set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
ax.set_title("(a) Net CO₂ emissions")
ax.grid(alpha=0.3)

# Panel 1: temperature
d_t = temp_anom(scen)
ax = axes[1]
ax.fill_between(d_t["Year"], d_t["T_p05"], d_t["T_p95"], color=color, alpha=0.25, lw=0)
ax.plot(d_t["Year"], d_t["T_med"], color=color, lw=2, label=scen)
ax.axhline(PARIS_15, color="#888", lw=0.8, ls="--")
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.set_xlim(2020, 2500)
ax.set_ylim(0, 2.5)
ax.set_ylabel("Temperature anomaly, K")
ax.set_title("(b) Temperature (rel. 1850–1900)")
ax.grid(alpha=0.3)

for ax in axes:
    ax.set_xlabel("Year")
    ax.text(2053, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
            fontsize=8, color="#999", ha="left")
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)

pl.suptitle("SSP1-VL: Very Low Emissions pathway", fontsize=12, fontweight="bold")
pl.tight_layout()
save(fig, "F01_vl_narrative.png")

# %% [markdown]
# ### F02 — L and LN: mitigation and overshoot

# %%
fig, axes = pl.subplots(1, 2, figsize=(10, 4))

for scen in ["L", "LN"]:
    color = SCEN_COLOR[scen]
    ls = "-" if scen == "L" else "--"

    d_co2 = get_emis(scen, "CO2 FFI")
    d_afolu = get_emis(scen, "CO2 AFOLU")
    net = (d_co2["Emissions"].values + d_afolu["Emissions"].values) / 1e6

    axes[0].plot(d_co2["Year"], net, color=color, lw=2, ls=ls, label=scen)

    d_t = temp_anom(scen)
    axes[1].fill_between(d_t["Year"], d_t["T_p05"], d_t["T_p95"], color=color, alpha=0.2, lw=0)
    axes[1].plot(d_t["Year"], d_t["T_med"], color=color, lw=2, ls=ls, label=scen)

axes[0].axhline(0, color="k", lw=0.5, ls=":")
axes[0].set_xlim(2020, 2500)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2500)
axes[1].set_ylim(0, 3)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

for ax in axes:
    ax.text(2053, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
            fontsize=8, color="#999", ha="left")
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)

pl.suptitle("SSP2-L and SSP2-LN: mitigation and overshoot", fontsize=12, fontweight="bold")
pl.tight_layout()
save(fig, "F02_l_ln_narrative.png")

# %% [markdown]
# ### F03 — ML and M: current-policy range

# %%
fig, axes = pl.subplots(1, 2, figsize=(10, 4))

for scen in ["ML", "M"]:
    color = SCEN_COLOR[scen]
    ls = "-" if scen == "ML" else "--"

    d_co2 = get_emis(scen, "CO2 FFI")
    d_afolu = get_emis(scen, "CO2 AFOLU")
    net = (d_co2["Emissions"].values + d_afolu["Emissions"].values) / 1e6

    axes[0].plot(d_co2["Year"], net, color=color, lw=2, ls=ls, label=scen)

    d_t = temp_anom(scen)
    axes[1].fill_between(d_t["Year"], d_t["T_p05"], d_t["T_p95"], color=color, alpha=0.2, lw=0)
    axes[1].plot(d_t["Year"], d_t["T_med"], color=color, lw=2, ls=ls, label=scen)

axes[0].axhline(0, color="k", lw=0.5, ls=":")
axes[0].set_xlim(2020, 2500)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2500)
axes[1].set_ylim(0, 7)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

for ax in axes:
    ax.text(2053, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
            fontsize=8, color="#999", ha="left")
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)

pl.suptitle("SSP2-ML and SSP2-M: current-policy range", fontsize=12, fontweight="bold")
pl.tight_layout()
save(fig, "F03_ml_m_narrative.png")

# %% [markdown]
# ### F04 — H and HL: high emissions and high CDR

# %%
fig, axes = pl.subplots(1, 2, figsize=(10, 4))

for scen in ["H", "HL"]:
    color = SCEN_COLOR[scen]
    ls = "-" if scen == "H" else "--"

    d_co2 = get_emis(scen, "CO2 FFI")
    d_afolu = get_emis(scen, "CO2 AFOLU")
    net = (d_co2["Emissions"].values + d_afolu["Emissions"].values) / 1e6

    axes[0].plot(d_co2["Year"], net, color=color, lw=2, ls=ls, label=scen)

    d_t = temp_anom(scen)
    axes[1].fill_between(d_t["Year"], d_t["T_p05"], d_t["T_p95"], color=color, alpha=0.2, lw=0)
    axes[1].plot(d_t["Year"], d_t["T_med"], color=color, lw=2, ls=ls, label=scen)

axes[0].axhline(0, color="k", lw=0.5, ls=":")
axes[0].set_xlim(2020, 2500)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2500)
axes[1].set_ylim(0, 10)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

for ax in axes:
    ax.text(2053, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
            fontsize=8, color="#999", ha="left")
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
pl.suptitle("SSP3-H and SSP5-HL: high emissions and high CDR", fontsize=12, fontweight="bold")
pl.tight_layout()
save(fig, "F04_h_hl_narrative.png")

# %% [markdown]
# ### F05 — SSP2-com vs. markers: global CO₂ + temperature

# %%
fig, axes = pl.subplots(1, 2, figsize=(12, 4.5))

# Left: net CO2 emissions all markers + SSP2-com
ax = axes[0]
for scen in SCEN_LABELS:
    d_ffi = get_emis(scen, "CO2 FFI")
    d_afolu = get_emis(scen, "CO2 AFOLU")
    net = (d_ffi["Emissions"].values + d_afolu["Emissions"].values) 
    mask = d_ffi["Year"] >= 2000
    ax.plot(d_ffi["Year"][mask], net[mask], color=SCEN_COLOR[scen], lw=1.5, alpha=0.7)
    ax.text(2101, net[mask][-1], scen, color=SCEN_COLOR[scen], va="center", fontsize=8)

ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(2000, 2102)
ax.set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
ax.set_title("(a) Net CO₂ emissions")
ax.grid(alpha=0.3)
ax.set_xlabel("Year")

# Right: temperature
ax = axes[1]
# Historical (use VL as representative for pre-2023 — same across scenarios)
d_hist = temp_anom("VL")
hist_mask = d_hist["Year"] <= HIST_END
ax.fill_between(d_hist.loc[hist_mask, "Year"],
                d_hist.loc[hist_mask, "T_p05"],
                d_hist.loc[hist_mask, "T_p95"],
                color=HIST_COLOR, alpha=0.0, lw=0)
ax.plot(d_hist.loc[hist_mask, "Year"], d_hist.loc[hist_mask, "T_med"],
        color=HIST_COLOR, lw=1.5)

for scen in SCEN_LABELS:
    d_t = temp_anom(scen)
    fut_mask = d_t["Year"] >= HIST_END
    ax.fill_between(d_t.loc[fut_mask, "Year"],
                    d_t.loc[fut_mask, "T_p05"],
                    d_t.loc[fut_mask, "T_p95"],
                    color=SCEN_COLOR[scen], alpha=0.0, lw=0)
    ax.plot(d_t.loc[fut_mask, "Year"], d_t.loc[fut_mask, "T_med"],
            color=SCEN_COLOR[scen], lw=1.5,label=scen)

ax.axhline(PARIS_15, color="#888", lw=0.8, ls="--")
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.set_xlim(2000, 2100)
ax.set_ylim(0.5, 5)
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("(b) Temperature")
ax.legend(loc="upper left")
ax.grid(alpha=0.3)
ax.set_xlabel("Year")

pl.tight_layout()
save(fig, "F05_trajectory_comparison.png")

# %%
d_ffi

# %% [markdown]
# ### F06 — All scenarios CO₂e 1950–2100 + SSP2-com

# %%
fig, ax = pl.subplots(figsize=(9, 5))

for scen in SCEN_LABELS:
    d = co2e_df[co2e_df["Scenario"] == scen]
    mask = d["Year"] >= 1950
    ax.plot(d.loc[mask, "Year"], d.loc[mask, "CO2e_emissions"] / 1e6,
            color=SCEN_COLOR[scen], lw=2, label=scen)

ax.axhline(0, color="k", lw=0.5, ls=":")
ax.axvline(HIST_END, color="#aaa", lw=1, ls=":")
ax.set_xlim(1950, 2102)
ax.set_xlabel("Year")
ax.set_ylabel("Total GHG emissions, GtCO₂e yr⁻¹")
ax.set_title("All scenarios: total GHG emissions to 2100")
ax.legend(ncol=2, fontsize=9)
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "F06_all_scenarios_co2e.png")

# %% [markdown]
# ### F07 — CH₄ and Sulfur 2000–2100

# %%
fig, axes = pl.subplots(1, 2, figsize=(10, 4))

for scen in SCEN_LABELS:
    d_ch4 = get_emis(scen, "CH4")
    mask_ch4 = (d_ch4["Year"] >= 2000).values
    axes[0].plot(d_ch4["Year"].values[mask_ch4], d_ch4["Emissions"].values[mask_ch4],
                 color=SCEN_COLOR[scen], lw=2, label=scen)

    d_s = get_emis(scen, "Sulfur")
    mask_s = (d_s["Year"] >= 2000).values
    axes[1].plot(d_s["Year"].values[mask_s], d_s["Emissions"].values[mask_s],
                 color=SCEN_COLOR[scen], lw=2)

axes[0].set_xlim(2000, 2100)
axes[0].set_ylabel("CH₄ emissions, Mt CH₄ yr⁻¹")
axes[0].set_title("(a) Methane")
axes[0].legend(ncol=2, fontsize=8)
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].set_xlim(2000, 2100)
axes[1].set_ylabel("Sulfur emissions, Mt S yr⁻¹")
axes[1].set_title("(b) Sulfur (aerosol precursor)")
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

pl.tight_layout()
save(fig, "F07_ch4_sulfur_2100.png")

def get_emis_from_ssp_cmip6(filepath, component):
    """Load emissions for a given component from an SSP CMIP6 file."""
    df = pd.read_csv(filepath, sep="\t", skiprows = [1,2,3])
    df.columns = df.columns.str.replace(' ', '')
    # Assume the file has columns "Year" and "Emissions"
    mult = 1
    if component == "Sulfur":
        component = "SO2"
    elif component == "CO2 FFI":
        component = "CO2"
        mult = (44.01 / 12.01)  # Convert from GtC to GtCO2
    elif component == "CO2 AFOLU":
        component = "CO2.1"
        mult = (44.01 / 12.01)  # Convert from GtC to GtCO2
    print(df.head())
    print(df.columns)
    years = df["Component"].values
    data = df[component].values * mult
    return years, data


def make_emissions_plots_with_ssp_overlay(component="Sulfur", endyear = 2100):


    
    fig, ax = pl.subplots(figsize=(8, 5))

    for scen in SCEN_LABELS:
        d = get_emis(scen, component)
        mask = (d["Year"] >= 2000) & (d["Year"] <= endyear)
        ax.plot(d.loc[mask, "Year"], d.loc[mask, "Emissions"],
                color=SCEN_COLOR[scen], lw=2, label=scen)


    ax.set_xlabel("Year")
    ax.set_ylabel(f"{component} emissions")
    ax.set_title(f"All scenarios: {component} emissions to {endyear}")

    ax.grid(alpha=0.3)

    ssp_path = "/home/masan/temp/rcmip_inputs_cscm/"
    for sspfile in glob.glob(f"{ssp_path}/ssp*_em_gases_vupdate_2024_WMO_added_new.txt"):
        ssp_name = os.path.basename(sspfile).split("_")[0]  # e.g. "ssp126"
        years, data = get_emis_from_ssp_cmip6(sspfile, component)
        ax.plot(years, data,
                lw=1.5, ls="--", label=f"{ssp_name} (CMIP6)")

    ax.set_xlim(2000, endyear)   
    ax.legend(ncol=2, fontsize=9)   
    pl.tight_layout()
    save(fig, f"Extra_trajectories_{component.lower()}_{endyear}.png")

comps_to_plot = ["CH4", "Sulfur", "BC", "OC", "CO2 FFI", "CO2 AFOLU"]
for comp in comps_to_plot:
    make_emissions_plots_with_ssp_overlay(component=comp, endyear=2150)
# %% [markdown]
# ### F08 — Temperature 2000–2100 (all scenarios + SSP2-com)

# %%
fig, ax = pl.subplots(figsize=(8, 5))

# Historical
d_hist = temp_anom("VL")
hist_mask = (d_hist["Year"] >= 2000) & (d_hist["Year"] <= HIST_END)
ax.fill_between(d_hist.loc[hist_mask, "Year"],
                d_hist.loc[hist_mask, "T_p05"],
                d_hist.loc[hist_mask, "T_p95"],
                color=HIST_COLOR, alpha=0.05, lw=0)
ax.plot(d_hist.loc[hist_mask, "Year"], d_hist.loc[hist_mask, "T_med"],
        color=HIST_COLOR, lw=1.5, label="Historical")

for scen in SCEN_LABELS:
    d_t = temp_anom(scen)
    fut_mask = (d_t["Year"] >= HIST_END) & (d_t["Year"] <= 2100)
    ax.fill_between(d_t.loc[fut_mask, "Year"],
                    d_t.loc[fut_mask, "T_p05"],
                    d_t.loc[fut_mask, "T_p95"],
                    color=SCEN_COLOR[scen], alpha=0.05, lw=0)
    ax.plot(d_t.loc[fut_mask, "Year"], d_t.loc[fut_mask, "T_med"],
            color=SCEN_COLOR[scen], lw=2, label=scen)

ax.axhline(PARIS_15, color="#888", lw=0.8, ls="--")
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.text(2101, PARIS_15, "1.5°C", va="center", fontsize=8, color="#888")
ax.text(2101, PARIS_20, "2.0°C", va="center", fontsize=8, color="#888")
ax.set_xlim(2000, 2102)
ax.set_ylim(0.5, 5.5)
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("Global mean temperature 2000–2100: all scenarios")
ax.legend(ncol=2, fontsize=9)
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "F08_temperature_2100.png")

# %% [markdown]
# ## Section 4 figures — FLEX extensions

# %% [markdown]
# ### F09 — CO₂ storyline types + per-scenario fossil 1750–2500

# %%
fig, axes = pl.subplots(1, 3, figsize=(18, 4.5))

# Left: analytic illustration of CS, ECS, CSCS shapes
ax = axes[0]
t = np.linspace(0, 400, 1000)

def sigmoid(t, t0, width):
    return 1 / (1 + np.exp(-(t - t0) / width))

# CS: constant then sigmoid to zero
cs = np.ones_like(t)
cs = cs * (1 - sigmoid(t, 200, 20))
ax.plot(t + 2100, cs * 10, lw=2, color="#2c7bb6", label="CS")

# ECS: exponential decay to plateau then sigmoid
ecs = np.exp(-t / 120) * 0.6 + 0.4
ecs = ecs * (1 - sigmoid(t, 220, 20))
ax.plot(t + 2100, ecs * 10, lw=2, color="#d7191c", label="ECS")

# CSCS: two-phase transition
cscs = 1 - sigmoid(t, 100, 15) * 0.5 - sigmoid(t, 280, 15) * 0.5
ax.plot(t + 2100, cscs * 10, lw=2, color="#1a9641", label="CSCS")

ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(2100, 2500)
ax.set_ylim(-1, 12)
ax.set_xlabel("Year")
ax.set_ylabel("CO₂ Total (schematic units)")
ax.set_title("(a) Storyline types: CS, ECS, CSCS")
ax.legend()
ax.grid(alpha=0.3)

# Middle: per-scenario AFOLU CO2 1750-2500
ax = axes[1]
for scen in SCEN_LABELS:
    d = get_emis(scen, "CO2 AFOLU")
    mask = d["Year"] >= 1900
    ax.plot(d["Year"][mask], d["Emissions"][mask] / 1e6,
            color=SCEN_COLOR[scen], lw=1.8, label=scen)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(1900, 2200)
ax.set_xlabel("Year")
ax.set_ylabel("CO₂ AFOLU, GtCO₂ yr⁻¹")
ax.set_title("(b) Per-scenario AFOLU CO₂, 1900–2200")
ax.legend(fontsize=8, ncol=2)
ax.grid(alpha=0.3)
ax.text(2077, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
        fontsize=8, color="#999", ha="left")

# Right: per-scenario fossil CO2 1750-2500
ax = axes[2]
for scen in SCEN_LABELS:
    d = get_emis(scen, "CO2 FFI")
    mask = d["Year"] >= 1900
    ax.plot(d["Year"][mask], d["Emissions"][mask] / 1e6,
            color=SCEN_COLOR[scen], lw=1.8, label=scen)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(1900, 2500)
ax.set_xlabel("Year")
ax.set_ylabel("CO₂ FFI, GtCO₂ yr⁻¹")
ax.set_title("(b) Per-scenario fossil CO₂, 1900–2500")
ax.legend(fontsize=8, ncol=2)
ax.grid(alpha=0.3)
ax.text(2052, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
        fontsize=8, color="#999", ha="left")

pl.tight_layout()
save(fig, "F09_storyline_types_CO2.png")

# %% [markdown]
# ### F10 — CDR by technology 2000–2500 (VL and HL)

# %%
if CDR_DATA:
    fig, axes = pl.subplots(1, 2, figsize=(11, 4.5))
    TECH_COLORS = {
        "BECCS":               "#2ca02c",
        "DACCS":               "#1f77b4",
        "Ocean CDR":           "#17becf",
        "Enhanced Weathering": "#8c564b",
        "Biochar":             "#e377c2",
        "Soil Carbon":         "#bcbd22",
    }

    for ax, scen in zip(axes, ["VL", "HL"]):
        if scen not in CDR_DATA:
            ax.text(0.5, 0.5, f"No CDR data for {scen}", transform=ax.transAxes, ha="center")
            continue
        df_cdr = CDR_DATA[scen]
        years = df_cdr.index.values
        mask = years >= 2000
        # Gross removals are negative numbers; plot as positive magnitude
        bottom = np.zeros(mask.sum())
        for tech in df_cdr.columns:
            vals = np.abs(df_cdr.loc[mask, tech].values)
            ax.bar(years[mask], vals, bottom=bottom, width=1,
                   color=TECH_COLORS.get(tech, "#aaa"), label=tech, alpha=0.85)
            bottom += vals
        ax.axvline(EXT_START, color="#555", lw=1, ls=":")
        ax.set_xlim(2000, 2500)
        ax.set_xlabel("Year")
        ax.set_ylabel("CDR, GtCO₂ yr⁻¹")
        ax.set_title(f"({['a','b'][['VL','HL'].index(scen)]}) {scen}")
        ax.grid(alpha=0.3, axis="y")
        if scen == "VL":
            ax.legend(fontsize=8, loc="upper right")

    pl.suptitle("CDR by technology 2000–2500", fontsize=12)
    pl.tight_layout()
    save(fig, "F10_cdr_technology.png")
else:
    # Fallback: show aggregate gross removals
    fig, ax = pl.subplots(figsize=(9, 4.5))
    for scen in ["VL", "LN", "L", "ML", "HL"]:
        scen_name = SCENARIO_META[scen]["scenario"]
        gr_mask = ((cont_df["scenario"] == scen_name) &
                   (cont_df["variable"] == "Emissions|CO2|Gross Removals"))
        gr_row = cont_df[gr_mask]
        if not gr_row.empty:
            year_cols = [c for c in gr_row.columns if str(c).replace(".","").isdigit()]
            years = np.array([float(c) for c in year_cols])
            vals  = gr_row[year_cols].values.flatten().astype(float)
            mask  = years >= 2000
            ax.plot(years[mask], np.abs(vals[mask]) / 1e6,
                    color=SCEN_COLOR[scen], lw=2, label=scen)
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":")
    ax.set_xlim(2000, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gross CDR, GtCO₂ yr⁻¹")
    ax.set_title("Gross CDR 2000–2500 (aggregate)")#; technology breakdown requires re-run of 5191)")
    ax.legend()
    ax.grid(alpha=0.3)
    pl.tight_layout()
    save(fig, "F10_cdr_aggregate.png")

# %% [markdown]
# ### F11 — CH₄ 1750–2500 with 2500 targets

# %%
# 2500 CH4 targets from config
CH4_TARGETS = {k: v.get("target") for k, v in cfg.component_global_targets.get("Emissions|CH4", {}).items()}
SO4_TARGETS = {k: v.get("target") for k, v in cfg.component_global_targets.get("Emissions|Sulfur", {}).items()}
fig, ax = pl.subplots(1,2, figsize=(12, 4.5))

for scen in SCEN_LABELS:
    d = get_emis(scen, "CH4")
    mask = d["Year"] >= 1900
    ax[0].plot(d["Year"][mask], d["Emissions"][mask],
            color=SCEN_COLOR[scen], lw=2, label=scen)
    d = get_emis(scen, "Sulfur")
    mask = d["Year"] >= 1900
    ax[1].plot(d["Year"][mask], d["Emissions"][mask],
            color=SCEN_COLOR[scen], lw=2, label=scen)
    # 2500 target marker
    if scen in CH4_TARGETS and CH4_TARGETS[scen] is not None:
        target = CH4_TARGETS[scen]
        ax[0].plot(2300, target, "o", color=SCEN_COLOR[scen], ms=6, zorder=5)
        # 2500 target marker
    if scen in SO4_TARGETS and SO4_TARGETS[scen] is not None:
        target = SO4_TARGETS[scen]
        ax[1].plot(2300, target, "o", color=SCEN_COLOR[scen], ms=6, zorder=5)

for ax_now in ax:
    ax_now.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
    ax_now.text(2102, ax_now.get_ylim()[1] * 0.97 if ax_now.get_ylim()[1] > 0 else 600,
            "← IAM | FLEX →", fontsize=8, color="#999", ha="left")
    ax_now.set_xlim(1900, 2310)
    ax_now.set_ylim(bottom=0)
    ax_now.set_xlabel("Year")
    ax_now.legend(fontsize=9, ncol=2)
    ax_now.grid(alpha=0.3)
ax[0].set_ylabel("CH₄ emissions, Mt CH₄ yr⁻¹")
ax[0].set_title("Methane emissions 1900–2300: IAM + FLEX extension\n(circles = 2500 targets)")
ax[0].set_ylabel("Sulfur emissions, Mt SO2 yr⁻¹")
ax[0].set_title("Sulfur emissions 1900–2300: IAM + FLEX extension\n(circles = 2500 targets)")
pl.tight_layout()
save(fig, "F11_ch4_1750_2500.png")

# %% [markdown]
# ### F12 — R5 regional CO₂ FFI disaggregation (VL and H)

# %%
fig, axes = pl.subplots(1, 2, figsize=(12, 4.5))

for ax, scen in zip(axes, ["VL", "H"]):
    r5_data = get_r5_emissions(scen, "Emissions|CO2|Energy and Industrial Processes")
    if not r5_data:
        ax.text(0.5, 0.5, f"Regional data not available for {scen}",
                transform=ax.transAxes, ha="center", fontsize=10)
        ax.set_title(f"({['a','b'][['VL','H'].index(scen)]}) {scen}")
        continue

    all_years = None
    stack_vals = []
    r5_order = ["OECD90", "REF", "ASIA", "MAF", "LAM"]
    for r5 in r5_order:
        if r5 in r5_data:
            yy, vv = r5_data[r5]
            if all_years is None:
                all_years = yy
            mask = (all_years >= 2020)
            if len(vv) == len(all_years):
                stack_vals.append((r5, vv[mask]))
            else:
                stack_vals.append((r5, np.zeros(mask.sum())))

    if all_years is not None:
        plot_years = all_years[all_years >= 2020]
        bottoms = np.zeros(len(plot_years))
        for r5, vals in stack_vals:
            ax.fill_between(plot_years, bottoms, bottoms + vals / 1e6,
                            color=R5_COLORS[r5], alpha=0.8, label=r5)
            bottoms = bottoms + vals / 1e6

    ax.axvline(EXT_START, color="#555", lw=1, ls=":")
    ax.axhline(0, color="k", lw=0.5, ls=":")
    ax.set_xlim(2020, 2500)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO₂ FFI, GtCO₂ yr⁻¹")
    panel = "a" if scen == "VL" else "b"
    ax.set_title(f"({panel}) {scen} — R5 regional breakdown")
    ax.grid(alpha=0.3, axis="y")
    if scen == "VL":
        ax.legend(fontsize=8)

pl.suptitle("Regional CO₂ FFI emissions 2020–2500 (R5 aggregation)", fontsize=12)
pl.tight_layout()
save(fig, "F12_r5_regional.png")

# %% [markdown]
# ### F13 — Temperature 1750–2500 (improved styling, Paris reference lines)

# %%
fig, ax = pl.subplots(figsize=(10, 5))

# Historical (pre-2023): black shading
d_hist = temp_anom("VL")
hist_mask = (d_hist["Year"] >= 1850) & (d_hist["Year"] <= HIST_END)
ax.fill_between(d_hist.loc[hist_mask, "Year"],
                d_hist.loc[hist_mask, "T_p05"],
                d_hist.loc[hist_mask, "T_p95"],
                color=HIST_COLOR, alpha=0.35, lw=0)
ax.plot(d_hist.loc[hist_mask, "Year"], d_hist.loc[hist_mask, "T_med"],
        color=HIST_COLOR, lw=1.5)

for scen in SCEN_LABELS:
    d_t = temp_anom(scen)
    fut_mask = d_t["Year"] >= HIST_END
    ax.fill_between(d_t.loc[fut_mask, "Year"],
                    d_t.loc[fut_mask, "T_p05"],
                    d_t.loc[fut_mask, "T_p95"],
                    color=SCEN_COLOR[scen], alpha=0.15, lw=0)
    ax.plot(d_t.loc[fut_mask, "Year"], d_t.loc[fut_mask, "T_med"],
            color=SCEN_COLOR[scen], lw=2, label=scen)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(PARIS_15, color="#888", lw=0.8, ls="--")
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.text(2505, PARIS_15, "1.5°C", va="center", fontsize=8, color="#888")
ax.text(2505, PARIS_20, "2.0°C", va="center", fontsize=8, color="#888")
ax.set_xlim(1850, 2510)
ax.set_ylim(-0.5, 9.)
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("Global mean temperature 1850–2500: all scenarios (median + 5–95%)")
ax.legend(fontsize=9, ncol=2, loc="upper left")
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "F13_temperature_2500.png")

# %% [markdown]
# ### F14 — Temperature ECDFs at 2100, 2300, maximum

# %%
fig, axes = pl.subplots(1, 3, figsize=(13, 4.5))
panels = ["(a) Temperature at 2100", "(b) Temperature at 2300", "(c) Maximum temperature"]
columns = ["Temp_2100_anomaly", "Temp_2300_anomaly", "Temp_max_anomaly"]

for ax, col, title in zip(axes, columns, panels):
    for scen in SCEN_LABELS:
        d = ecdf_df[ecdf_df["Scenario"] == scen][col].dropna().values
        d_sorted = np.sort(d)
        p = np.linspace(0, 100, len(d_sorted))
        ax.plot(d_sorted, p, color=SCEN_COLOR[scen], lw=1.8, label=scen)

    for ref in [PARIS_15, PARIS_20, 3.0, 4.0]:
        ax.axvline(ref, color="#ccc", lw=0.7, ls="--", zorder=0)
    ax.axhline(50, color="#bbb", lw=0.5, ls=":")
    ax.axhline(5,  color="#ddd", lw=0.5, ls=":")
    ax.axhline(95, color="#ddd", lw=0.5, ls=":")
    ax.set_xlabel("Temperature anomaly, K (rel. 1850–1900)")
    ax.set_ylabel("Cumulative probability, %")
    ax.set_ylim(0, 100)
    ax.set_title(title)
    ax.grid(alpha=0.2)

axes[2].legend(fontsize=8, loc="lower right")
pl.tight_layout()
save(fig, "F14_temperature_ecdfs.png")


# %% [markdown]
# ### F15 — Ozone exploration figure

# %%
fig, axes = pl.subplots(3, 2, figsize=(15, 15))
panels = ["(a) Ozone ERF", "(b) NOx emissions", "(c) CH4 concentration",
          "(d) VOC emissions", "(e) CO emissions", "(f) EESC concentration"]
columns = ["Ozone", "NOx", "CH4", "VOC", "CO", "Equivalent effective stratospheric chlorine"]
units = ["W m⁻²", "Mt NOx yr⁻¹", "ppb", "Mt VOC yr⁻¹", "Mt CO yr⁻¹", "ppb"]
for i, (col, title) in enumerate(zip(columns, panels)):
    ax = axes[i // 2, i % 2]
    for scen in SCEN_LABELS:
        if "emissions" in title.lower():
            d = get_emis(scen, col)
            col_use = "Emissions"
        elif "concentration" in title.lower():
            d = get_emis(scen, col, dataframe=conc_df)
            col_use = "Concentration_median"
        else:
            d = get_emis(scen, col, dataframe=forcing_persp_df)
            col_use = "Forcing_median"
        mask = (d["Year"] >= 1850) & (d["Year"] <= 2500)
        print(d.columns)
        if d.shape[0] == 0:
            print(f"No data for {scen} and {col}")
            print(d.head())
            print(col)
            print(emis_df["Species"].unique())
            sys.exit(4)
        ax.plot(d.loc[mask, "Year"], d.loc[mask, col_use],
                color=SCEN_COLOR[scen], lw=2, label=scen)
        if col_use.endswith("median"):
            print("Hello, plotting uncertainty for", col, "in scenario", scen)
            ax.fill_between(d.loc[mask, "Year"],
                            d.loc[mask, col_use.replace("median", "p05")],
                            d.loc[mask, col_use.replace("median", "p95")],
                            color=SCEN_COLOR[scen], alpha=0.15, lw=0)
            #print(d.loc[mask, col_use.replace("median", "p05")].tail())
            #print(d.loc[mask, col_use.replace("median", "p95")].tail())
            #sys.exit(4)
    ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
    #ax.axhline(0, color="k", lw=0.5, ls=":")


    ax.set_xlabel("Year")
    ax.set_ylabel(f"{col} ({units[columns.index(col)]})")
    ax.set_title(title, fontsize=12)

    ax.grid(alpha=0.3)
    ax.set_xlim(1850, 2500)   
    ax.legend(ncol=2, fontsize=9)   
pl.tight_layout()
save(fig, f"Ozone_stability_exploration.png")
#axes[2].legend(fontsize=8, loc="lower right")


# %% [markdown]
# ## Summary

# %%
print("\n" + "=" * 60)
print(f"All figures saved to: {PLOTS_DIR}")
print("=" * 60)
for f in sorted(PLOTS_DIR.glob("*.png")):
    print(f"  {f.name}")
