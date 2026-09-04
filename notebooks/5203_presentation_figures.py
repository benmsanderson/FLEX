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
from pathlib import Path

import matplotlib.pyplot as pl
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from flex.config import load_config, DATA_DIR, FAIR_PARAMS_FILE, FAIR_SPECIES_FILE, FAIR_FORCING_FILE

warnings.filterwarnings("ignore", message="All-NaN slice encountered")

cfg = load_config(config_name)
wcfg = load_config(wiemip_config)

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
    pl.show()
    pl.close(fig)


# %% [markdown]
# ## A — Load scenariomip_default outputs

# %%
temp_df     = pd.read_csv(OUTPUTS_DIR / "fair_temperature_1750-2500.csv")
emis_df     = pd.read_csv(OUTPUTS_DIR / "fair_emissions_by_species.csv")
co2e_df     = pd.read_csv(OUTPUTS_DIR / "fair_co2e_emissions_1750-2500.csv")
ecdf_df     = pd.read_csv(OUTPUTS_DIR / "fair_temperature_ecdf_data.csv")
forcing_df  = pd.read_csv(OUTPUTS_DIR / "fair_forcing_sum_1750-2500.csv")
conc_df     = pd.read_csv(OUTPUTS_DIR / "fair_concentration_ghgs_1750-2500.csv")
cont_df     = pd.read_csv(OUTPUTS_DIR / "continuous_emissions_timeseries_1750_2500.csv")

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
def get_emis(scenario, species):
    return emis_df[(emis_df["Scenario"] == scenario) & (emis_df["Species"] == species)]

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

# %% [markdown]
# ## B — Load WIEMIP outputs

# %%
w_temp_df = pd.read_csv(WIEMIP_DIR / "fair_temperature_1750-2500.csv")
w_emis_df = pd.read_csv(WIEMIP_DIR / "fair_emissions_by_species.csv")

# WIEMIP scenarios include source + CF pairs
WIEMIP_SCENS = sorted(w_temp_df["Scenario"].unique())
print("WIEMIP scenarios:", WIEMIP_SCENS)

# Compute WIEMIP baselines (source scenarios share baseline with default)
W_BASELINE = {}
for s in WIEMIP_SCENS:
    src = s.replace("-CF", "")
    if src in BASELINE:
        W_BASELINE[s] = BASELINE[src]
    else:
        mask = (w_temp_df["Scenario"] == s) & (w_temp_df["Year"] >= 1850) & (w_temp_df["Year"] <= 1900)
        W_BASELINE[s] = w_temp_df.loc[mask, "Temperature_median"].mean()

def w_temp_anom(scenario):
    d = w_temp_df[w_temp_df["Scenario"] == scenario].copy()
    bl = W_BASELINE[scenario]
    d["T_med"] = d["Temperature_median"] - bl
    d["T_p05"] = d["Temperature_p05"] - bl
    d["T_p95"] = d["Temperature_p95"] - bl
    return d

# Read optimization results for target temperatures
import json
opt_file = WIEMIP_DIR / "optimization_results_handtuned.json"
if not opt_file.exists():
    opt_file = WIEMIP_DIR / "optimization_results.json"
with open(opt_file) as fh:
    opt_data = json.load(fh)["optimization_results"]

CF_PAIRS = [(s.replace("-CF", ""), s) for s in opt_data if s.endswith("-CF")]
print("CF pairs:", CF_PAIRS)

# %% [markdown]
# ## C — SSP2-com: load, interpolate, run FaIR (full 1000-member ensemble)

# %%
# Load SSP2-com future emissions (2023-2100, 5-year intervals)
com_fut = pd.read_excel(SSP2COM_DIR / "ssp2-com_world_total.xlsx")
com_hist = pd.read_excel(SSP2COM_DIR / "hist_world_total.xlsx")

print("SSP2-com future variables:", com_fut["Variable"].tolist())
print("SSP2-com hist variables:", com_hist["Variable"].tolist()[:8])

# %%
# Build annual interpolated timeseries for each species
# Year columns in future file are strings like '2023', '2030', etc.
def get_com_series(fut_df, hist_df, variable, hist_variable=None):
    """
    Return (years, values) annual array 1750–2100 for the given variable.
    Uses hist_df for 1750–2022, fut_df for 2023–2100 (interpolated).
    hist_variable defaults to variable if not provided.
    """
    if hist_variable is None:
        hist_variable = variable

    # --- Future: 5-year → annual via cubic spline ---
    fut_row = fut_df[fut_df["Variable"] == variable]
    if fut_row.empty:
        return None, None
    year_cols = [c for c in fut_df.columns if str(c).isdigit()]
    fut_years = np.array([int(c) for c in year_cols])
    fut_vals  = fut_row[year_cols].values.flatten().astype(float)
    cs = CubicSpline(fut_years, fut_vals, extrapolate=False)
    ann_years_fut = np.arange(2023, 2101)
    ann_vals_fut  = cs(ann_years_fut)
    # Clamp: CO2 AFOLU can go negative, others generally not below -1e4
    ann_vals_fut = np.where(np.isnan(ann_vals_fut), 0.0, ann_vals_fut)

    # --- Historical ---
    hist_row = hist_df[hist_df["Variable"] == hist_variable]
    if hist_row.empty:
        # No history: use zeros
        hist_years = np.arange(1750, 2023)
        hist_vals  = np.zeros_like(hist_years, dtype=float)
    else:
        h_year_cols = [c for c in hist_df.columns if str(c).isdigit()]
        hist_years = np.array([int(c) for c in h_year_cols])
        hist_vals  = hist_row[h_year_cols].values.flatten().astype(float)
        # Restrict to 1750–2022
        mask = hist_years < 2023
        hist_years = hist_years[mask]
        hist_vals  = hist_vals[mask]
        # Fill leading NaN with the first valid value (or 0 if all NaN)
        first_valid = np.where(~np.isnan(hist_vals))[0]
        if len(first_valid) == 0:
            hist_vals[:] = 0.0
        elif first_valid[0] > 0:
            hist_vals[:first_valid[0]] = hist_vals[first_valid[0]]
        # Fill any remaining NaN (gaps) by linear interpolation
        nan_mask = np.isnan(hist_vals)
        if nan_mask.any():
            hist_vals[nan_mask] = np.interp(hist_years[nan_mask], hist_years[~nan_mask], hist_vals[~nan_mask])

    all_years = np.concatenate([hist_years, ann_years_fut])
    all_vals  = np.concatenate([hist_vals,  ann_vals_fut])
    return all_years, all_vals

# Test
yy, vv = get_com_series(com_fut, com_hist,
                         "Emissions|CO2|Energy and Industrial Processes",
                         "Emissions|CO2|Energy and Industrial Processes")
if yy is not None:
    print(f"CO2 FFI series: {len(yy)} years, range {yy[0]:.0f}–{yy[-1]:.0f}, "
          f"2023={vv[np.argmin(abs(yy-2023))]:.0f} Mt, 2100={vv[-1]:.0f} Mt")

# %%
# Map SSP2-com variable names → FaIR species names and units
# FaIR native names from the existing emissions CSV
COM_TO_FAIR = {
    "Emissions|CO2|Energy and Industrial Processes": ("CO2 FFI",   "Emissions|CO2|Energy and Industrial Processes"),
    "Emissions|CO2|AFOLU":                           ("CO2 AFOLU", "Emissions|CO2|AFOLU"),
    "Emissions|CH4":                                 ("CH4",       "Emissions|CH4"),
    "Emissions|N2O":                                 ("N2O",       "Emissions|N2O"),
    "Emissions|Sulfur":                              ("Sulfur",    "Emissions|Sulfur"),
    "Emissions|BC":                                  ("BC",        "Emissions|BC"),
    "Emissions|OC":                                  ("OC",        "Emissions|OC"),
    "Emissions|NH3":                                 ("NH3",       "Emissions|NH3"),
    "Emissions|NOx":                                 ("NOx",       "Emissions|NOx"),
    "Emissions|CO":                                  ("CO",        "Emissions|CO"),
    "Emissions|VOC":                                 ("VOC",       "Emissions|VOC"),
    "Emissions|HFC|HFC125":                          ("HFC-125",   None),
    "Emissions|HFC|HFC134a":                         ("HFC-134a",  None),
    "Emissions|HFC|HFC143a":                         ("HFC-143a",  None),
    "Emissions|HFC|HFC227ea":                        ("HFC-227ea", None),
    "Emissions|HFC|HFC23":                           ("HFC-23",    None),
    "Emissions|HFC|HFC245fa":                        ("HFC-245fa", None),
    "Emissions|HFC|HFC32":                           ("HFC-32",    None),
    "Emissions|HFC|HFC43-10":                        ("HFC-4310mee", None),
    "Emissions|PFC|C2F6":                            ("C2F6",      None),
    "Emissions|PFC|C6F14":                           ("C6F14",     None),
    "Emissions|PFC|CF4":                             ("CF4",       None),
    "Emissions|SF6":                                 ("SF6",       None),
}

# Build annual time-value dict for SSP2-com overrides
com_annual = {}
for com_var, (fair_specie, hist_var) in COM_TO_FAIR.items():
    yy, vv = get_com_series(com_fut, com_hist, com_var, hist_var)
    if yy is not None:
        com_annual[fair_specie] = (yy, vv)

print("SSP2-com species resolved:", list(com_annual.keys()))

# %%
import pooch
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties

params_file = FAIR_PARAMS_FILE
species_file = str(FAIR_SPECIES_FILE)
forcing_file = str(FAIR_FORCING_FILE)
emis_file    = str(OUTPUTS_DIR / "emissions_1750-2500.csv")  # use ML as template

# SSP2-com FaIR run: set up with [ML, SSP2-com], fill from pipeline CSV, copy ML to SSP2-com, override.
COM_SCEN = "SSP2-com"
TEMPLATE_SCEN = "ML"   # closest marker; used for species not in SSP2-com

f_com = FAIR()
f_com.define_time(1750, 2101, 1)   # only to 2100 — SSP2-com doesn't extend beyond
f_com.define_scenarios([TEMPLATE_SCEN, COM_SCEN])
species, properties = read_properties(species_file)
f_com.define_species(species, properties)
f_com.ch4_method = "Thornhill2021"

df_configs = pd.read_csv(params_file, index_col=0)
print(f"Full ensemble: {len(df_configs)} members")
f_com.define_configs(df_configs.index)
f_com.allocate()

# fill_from_csv needs SSP2-com rows in both the emissions and forcing CSVs.
# Build combined temp files by copying ML rows and relabelling as SSP2-com.
import tempfile, os as _os

def _add_com_rows(raw_df, scen_col, template, com):
    ml_rows = raw_df[raw_df[scen_col] == template].copy()
    ml_rows[scen_col] = com
    return pd.concat([raw_df, ml_rows], ignore_index=True)

_emis_raw    = pd.read_csv(emis_file)
_forcing_raw = pd.read_csv(forcing_file)

# Copy ML rows as SSP2-com
_combined_emis = _add_com_rows(_emis_raw, "scenario", TEMPLATE_SCEN, COM_SCEN)

# Embed SSP2-com species overrides directly into the combined emissions CSV.
# The CSV has midyear columns like "1750.5", "1751.5", ...
_yr_cols = [c for c in _combined_emis.columns
            if isinstance(c, (int, float)) or
            (isinstance(c, str) and c.replace(".", "").lstrip("-").isdigit())]
_yr_floats = np.array([float(c) for c in _yr_cols])

# Only override FUTURE years (>= 2023) to keep the same historical emissions as
# the ScenarioMIP pipeline.  The historical period (1750–2022) retains ML's values
# so both runs share the same pre-2023 forcing and temperature state.
_future_mask = _yr_floats >= 2023.5
_yr_cols_fut  = [c for c, flag in zip(_yr_cols, _future_mask) if flag]
_yr_floats_fut = _yr_floats[_future_mask]

for _fair_sp, (_yy, _vv) in com_annual.items():
    # Interpolate annual values (integer years) onto midyear CSV columns (future only)
    _interp = np.interp(_yr_floats_fut, _yy + 0.5, _vv,
                        left=float(_vv[0]), right=float(_vv[-1]))
    _mask = (_combined_emis["scenario"] == COM_SCEN) & (_combined_emis["variable"] == _fair_sp)
    if _mask.any():
        _combined_emis.loc[_mask, _yr_cols_fut] = _interp
        print(f"  Embedded override for {_fair_sp} ({_mask.sum()} rows)")

# Forcing file uses capital "Scenario"
_forcing_scen_col = "Scenario" if "Scenario" in _forcing_raw.columns else "scenario"
_combined_forcing = _add_com_rows(_forcing_raw, _forcing_scen_col, TEMPLATE_SCEN, COM_SCEN)

_tmp_files = []
try:
    for _df, _suffix in [(_combined_emis, "_emis.csv"), (_combined_forcing, "_forcing.csv")]:
        with tempfile.NamedTemporaryFile(suffix=_suffix, delete=False, mode="w") as _tmp:
            _df.to_csv(_tmp, index=False)
            _tmp_files.append(_tmp.name)
    _tmp_emis_path, _tmp_forcing_path = _tmp_files
    f_com.fill_from_csv(forcing_file=_tmp_forcing_path, emissions_file=_tmp_emis_path)
finally:
    for _p in _tmp_files:
        _os.unlink(_p)

# Zero out solar for both scenarios (as in 5201)
for _scen in [COM_SCEN, TEMPLATE_SCEN]:
    try:
        f_com.forcing.loc[dict(scenario=_scen, specie="Solar")] = 0
    except Exception:
        pass
print("Emissions and forcing filled.")

# %%
print("Running FaIR for SSP2-com (full ensemble) …")
f_com.fill_species_configs(species_file)
f_com.override_defaults(str(params_file))
f_com.climate_configs["stochastic_run"][:] = False
initialise(f_com.concentration, f_com.species_configs["baseline_concentration"])
initialise(f_com.forcing, 0)
initialise(f_com.temperature, 0)
initialise(f_com.cumulative_emissions, 0)
initialise(f_com.airborne_emissions, 0)
initialise(f_com.ocean_heat_content_change, 0)
f_com.run()
print("Done.")

# %%
# Extract SSP2-com temperature
com_temp_data = f_com.temperature.sel(scenario=COM_SCEN, layer=0)
com_baseline  = float(com_temp_data.sel(timebounds=slice(1850, 1900)).mean())
com_temp = pd.DataFrame({
    "Year":  f_com.timebounds,
    "T_med": com_temp_data.median(dim="config").values - com_baseline,
    "T_p05": com_temp_data.quantile(0.05, dim="config").values - com_baseline,
    "T_p95": com_temp_data.quantile(0.95, dim="config").values - com_baseline,
})

print(f"SSP2-com 2100 median temperature anomaly: "
      f"{float(com_temp.loc[com_temp.Year==2100, 'T_med'].iloc[0]):.2f} °C")

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
    if not candidates:
        # Try partial match
        candidates = list(OUTPUTS_DIR.glob("extensions_*.csv"))
        candidates = [c for c in candidates if scen_label in c.stem or
                      SCENARIO_META[scen_label]["model"].split()[0] in c.stem]
    if not candidates:
        print(f"  No extension file found for {scen_label}")
        return {}

    df_ext = pd.read_csv(candidates[0])
    var_mask = df_ext["variable"] == variable
    result = {}
    for r5 in R5_MAP:
        r5_total = None
        for _, row in df_ext[var_mask].iterrows():
            region = row["region"]
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

# %% [markdown]
# ## Section 3 figures — ScenarioMIP to 2100

# %% [markdown]
# ### F01 — VL narrative: CO₂ components + temperature (2020–2100)

# %%
fig, axes = pl.subplots(1, 3, figsize=(13, 4))

scen = "VL"
color = SCEN_COLOR[scen]

# Panel 0: CO2 FFI
d_ffi = get_emis(scen, "CO2 FFI")
ax = axes[0]
ax.plot(d_ffi["Year"], d_ffi["Emissions"] / 1e6, color=color, lw=2)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(2020, 2100)
ax.set_ylabel("CO₂ FFI, GtCO₂ yr⁻¹")
ax.set_title("(a) Fossil CO₂")
ax.grid(alpha=0.3)

# Panel 1: CO2 AFOLU
d_afolu = get_emis(scen, "CO2 AFOLU")
ax = axes[1]
ax.plot(d_afolu["Year"], d_afolu["Emissions"] / 1e6, color=color, lw=2)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(2020, 2100)
ax.set_ylabel("CO₂ AFOLU, GtCO₂ yr⁻¹")
ax.set_title("(b) AFOLU CO₂")
ax.grid(alpha=0.3)

# Panel 2: temperature
d_t = temp_anom(scen)
ax = axes[2]
ax.fill_between(d_t["Year"], d_t["T_p05"], d_t["T_p95"], color=color, alpha=0.25, lw=0)
ax.plot(d_t["Year"], d_t["T_med"], color=color, lw=2, label=scen)
ax.axhline(PARIS_15, color="#888", lw=0.8, ls="--")
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.set_xlim(2020, 2100)
ax.set_ylim(0, 3)
ax.set_ylabel("Temperature anomaly, K")
ax.set_title("(c) Temperature (rel. 1850–1900)")
ax.grid(alpha=0.3)

for ax in axes:
    ax.set_xlabel("Year")

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
axes[0].set_xlim(2020, 2100)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2100)
axes[1].set_ylim(0, 3)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

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
axes[0].set_xlim(2020, 2100)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2100)
axes[1].set_ylim(0, 4)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

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
axes[0].set_xlim(2020, 2100)
axes[0].set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
axes[0].set_title("(a) Net CO₂ emissions")
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_xlabel("Year")

axes[1].axhline(PARIS_15, color="#888", lw=0.8, ls="--")
axes[1].axhline(PARIS_20, color="#888", lw=0.8, ls="--")
axes[1].set_xlim(2020, 2100)
axes[1].set_ylim(0, 5)
axes[1].set_ylabel("Temperature anomaly, K")
axes[1].set_title("(b) Temperature (rel. 1850–1900)")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].set_xlabel("Year")

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

# SSP2-com net CO2
com_ffi_years, com_ffi = com_annual.get("CO2 FFI", (None, None))
com_afolu_years, com_afolu = com_annual.get("CO2 AFOLU", (None, None))
if com_ffi_years is not None and com_afolu_years is not None:
    net_com = (com_ffi + com_afolu)/1e3
    mask_com = com_ffi_years >= HIST_END
    ax.plot(com_ffi_years[mask_com], net_com[mask_com],
            color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com", zorder=5)
    ax.text(2101, net_com[mask_com][-1], "COM", color=COM_COLOR, va="center", fontsize=8)

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

# SSP2-com temperature (median only — no shading to reduce clutter)
com_fut_mask = com_temp["Year"] >= HIST_END
ax.plot(com_temp.loc[com_fut_mask, "Year"], com_temp.loc[com_fut_mask, "T_med"],
        color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com")

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
save(fig, "F05_ssp2com_comparison.png")

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

# SSP2-com CO2e: rough estimate from CO2 FFI + AFOLU (dominant terms)
if com_ffi_years is not None:
    # Use CO2 + CH4 GWP approx as a simple CO2e
    com_ch4_yy, com_ch4_vv = com_annual.get("CH4", (None, None))
    com_n2o_yy, com_n2o_vv = com_annual.get("N2O", (None, None))
    net_co2 = (com_ffi + com_afolu)
    ch4_co2e = com_ch4_vv * 29.8 if com_ch4_vv is not None else 0  # AR6 GWP100
    n2o_co2e = com_n2o_vv * 273   if com_n2o_vv is not None else 0  # AR6 GWP100 (kt→Mt: /1000)
    if com_n2o_vv is not None:
        n2o_co2e = n2o_co2e / 1000  # kt N2O → Mt CO2e
    total_co2e = (net_co2 + ch4_co2e + n2o_co2e) / 1e6
    mask_com = com_ffi_years >= HIST_END
    ax.plot(com_ffi_years[mask_com], total_co2e[mask_com]*1000,
            color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com", zorder=5)

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

# SSP2-com overlays
com_ch4_yy, com_ch4_vv = com_annual.get("CH4", (None, None))
com_s_yy, com_s_vv = com_annual.get("Sulfur", (None, None))
if com_ch4_yy is not None:
    mask_c = com_ch4_yy >= HIST_END
    axes[0].plot(com_ch4_yy[mask_c], com_ch4_vv[mask_c],
                 color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com")
if com_s_yy is not None:
    mask_s = com_s_yy >= HIST_END
    axes[1].plot(com_s_yy[mask_s], com_s_vv[mask_s],
                 color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com")

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

# SSP2-com
fut_mask_c = (com_temp["Year"] >= HIST_END) & (com_temp["Year"] <= 2100)
ax.fill_between(com_temp.loc[fut_mask_c, "Year"],
                com_temp.loc[fut_mask_c, "T_p05"],
                com_temp.loc[fut_mask_c, "T_p95"],
                color=COM_COLOR, alpha=0.2, lw=0)
ax.plot(com_temp.loc[fut_mask_c, "Year"], com_temp.loc[fut_mask_c, "T_med"],
        color=COM_COLOR, lw=2.5, ls="--", label="SSP2-com")

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
fig, axes = pl.subplots(1, 2, figsize=(12, 4.5))

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
ax.set_ylabel("CO₂ FFI (schematic units)")
ax.set_title("(a) Storyline types: CS, ECS, CSCS")
ax.legend()
ax.grid(alpha=0.3)

# Right: per-scenario fossil CO2 1750-2500
ax = axes[1]
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
ax.text(2102, ax.get_ylim()[1] * 0.95, "← IAM | FLEX →",
        fontsize=8, color="#999", ha="left")

pl.tight_layout()
save(fig, "F09_storyline_types_fossil.png")

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
    ax.set_title("Gross CDR 2000–2500 (aggregate; technology breakdown requires re-run of 5191)")
    ax.legend()
    ax.grid(alpha=0.3)
    pl.tight_layout()
    save(fig, "F10_cdr_aggregate.png")

# %% [markdown]
# ### F11 — CH₄ 1750–2500 with 2500 targets

# %%
# 2500 CH4 targets from config
CH4_TARGETS = {k: v.get("target") for k, v in cfg.component_global_targets.get("Emissions|CH4", {}).items()}

fig, ax = pl.subplots(figsize=(9, 4.5))

for scen in SCEN_LABELS:
    d = get_emis(scen, "CH4")
    mask = d["Year"] >= 1900
    ax.plot(d["Year"][mask], d["Emissions"][mask],
            color=SCEN_COLOR[scen], lw=2, label=scen)
    # 2500 target marker
    if scen in CH4_TARGETS and CH4_TARGETS[scen] is not None:
        target = CH4_TARGETS[scen]
        ax.plot(2500, target, "o", color=SCEN_COLOR[scen], ms=6, zorder=5)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.text(2102, ax.get_ylim()[1] * 0.97 if ax.get_ylim()[1] > 0 else 600,
        "← IAM | FLEX →", fontsize=8, color="#999", ha="left")
ax.set_xlim(1900, 2510)
ax.set_ylim(bottom=0)
ax.set_xlabel("Year")
ax.set_ylabel("CH₄ emissions, Mt CH₄ yr⁻¹")
ax.set_title("Methane emissions 1900–2500: IAM + FLEX extension\n(circles = 2500 targets)")
ax.legend(fontsize=9, ncol=2)
ax.grid(alpha=0.3)
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
ax.set_ylim(-0.5, 6.5)
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
# ## Section 5 figures — WIEMIP counterfactuals

# %% [markdown]
# ### S01 — WIEMIP pair schematic: overshoot vs. maintain-peak

# %%
fig, ax = pl.subplots(figsize=(7, 4))
t = np.linspace(0, 200, 500)

# Overshoot (HL-like): rises, peaks, declines
t_peak_os = 80
hl_curve = (np.exp(-((t - t_peak_os) / 30)**2) * 2.0
            + 0.5 * (1 - np.exp(-t / 30))
            + 0.3 * np.maximum(0, 1 - (t - t_peak_os) / 100))

# Maintain-peak (CF): rises to same peak but stays there with CDR
t_peak_cf = 100
cf_curve  = np.minimum(hl_curve.max() * 0.85,
                        hl_curve * 0.85 + 0.1 * np.maximum(0, t - t_peak_cf) / 10)
cf_curve  = np.minimum(cf_curve, hl_curve.max() * 0.85)

ax.fill_between(t + 2023, hl_curve, cf_curve,
                where=hl_curve > cf_curve, color="#ff9999", alpha=0.3, label="Attributable difference")
ax.plot(t + 2023, hl_curve, color=SCEN_COLOR["HL"], lw=2.5, label="HL (overshoot)")
ax.plot(t + 2023, cf_curve, color=SCEN_COLOR["HL"], lw=2.5, ls="--", label="HL-CF (maintain peak)")

ax.axhline(PARIS_20, color="#888", lw=0.8, ls=":")
ax.text(2225, PARIS_20 + 0.05, "Target temperature", va="bottom", fontsize=9, color="#888")

ax.set_xlim(2023, 2223)
ax.set_ylim(0.5, 3.5)
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("WIEMIP schematic: overshoot vs. maintain-peak-warming")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "S01_wiemip_schematic.png")

# %% [markdown]
# ### F15 — WIEMIP CO₂ emissions: source/CF pairs

# %%
def ls_for(scen):
    return "--" if scen.endswith("-CF") else "-"

def color_for(scen):
    src = scen.replace("-CF", "")
    return SCEN_COLOR.get(src, "#888")

fig, ax = pl.subplots(figsize=(9, 5))

for src, cf in CF_PAIRS:
    for scen in [src, cf]:
        d_ffi = w_emis_df[(w_emis_df["Scenario"] == scen) & (w_emis_df["Species"] == "CO2 FFI")]
        d_afolu = w_emis_df[(w_emis_df["Scenario"] == scen) & (w_emis_df["Species"] == "CO2 AFOLU")]
        if d_ffi.empty:
            continue
        net = (d_ffi["Emissions"].values + d_afolu["Emissions"].values) / 1e6
        mask = d_ffi["Year"] >= 1990
        ax.plot(d_ffi["Year"][mask], net[mask],
                color=color_for(scen), lw=2, ls=ls_for(scen),
                label=scen)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(1990, 2300)
ax.set_xlabel("Year")
ax.set_ylabel("Net CO₂ (FFI + AFOLU), GtCO₂ yr⁻¹")
ax.set_title("WIEMIP: source and counterfactual CO₂ emissions\n(solid: source; dashed: CF)")
ax.legend(fontsize=9, ncol=2)
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "F15_wiemip_co2_emissions.png")

# %% [markdown]
# ### F16 — WIEMIP temperature: source/CF pairs with targets

# %%
fig, ax = pl.subplots(figsize=(9, 5))

for src, cf in CF_PAIRS:
    target_temp = opt_data[cf]["target_temp"]
    color = color_for(cf)

    for scen in [src, cf]:
        d_t = w_temp_anom(scen)
        fut_mask = d_t["Year"] >= 1990
        ax.fill_between(d_t.loc[fut_mask, "Year"],
                        d_t.loc[fut_mask, "T_p05"],
                        d_t.loc[fut_mask, "T_p95"],
                        color=color, alpha=0.12, lw=0)
        ax.plot(d_t.loc[fut_mask, "Year"], d_t.loc[fut_mask, "T_med"],
                color=color, lw=2, ls=ls_for(scen), label=scen)

    # Target reference line (adjusted for baseline offset of source scenario)
    src_d = w_temp_df[w_temp_df["Scenario"] == src]
    src_bl = src_d[(src_d["Year"] >= 1850) & (src_d["Year"] <= 1900)]["Temperature_median"].mean()
    target_anom = target_temp - src_bl
    ax.axhline(target_anom, color=color, lw=1, ls=":", alpha=0.7)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(0, color="k", lw=0.5, ls=":")
ax.set_xlim(1990, 2300)
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("WIEMIP: temperature outcomes — source (solid) vs. counterfactual (dashed)\n(dotted: prescribed target)")
ax.legend(fontsize=9, ncol=2)
ax.grid(alpha=0.3)
pl.tight_layout()
save(fig, "F16_wiemip_temperature.png")

# %% [markdown]
# ### F17 — HL vs HL-CF: attributed temperature difference (AR7-WG1-CH9)

# %%
fig, axes = pl.subplots(1, 2, figsize=(12, 4.5))

# Left: full temperature traces
ax = axes[0]
for scen, lw, ls, label in [("HL", 2.5, "-", "HL (overshoot)"),
                              ("HL-CF", 2.5, "--", "HL-CF (maintain peak)")]:
    if scen not in w_temp_df["Scenario"].values:
        continue
    d_t = w_temp_anom(scen)
    fut_mask = d_t["Year"] >= 2000
    ax.fill_between(d_t.loc[fut_mask, "Year"],
                    d_t.loc[fut_mask, "T_p05"],
                    d_t.loc[fut_mask, "T_p95"],
                    color=color_for(scen), alpha=0.15, lw=0)
    ax.plot(d_t.loc[fut_mask, "Year"], d_t.loc[fut_mask, "T_med"],
            color=color_for(scen), lw=lw, ls=ls, label=label)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.axhline(PARIS_20, color="#888", lw=0.8, ls="--")
ax.set_xlim(2000, 2300)
ax.set_xlabel("Year")
ax.set_ylabel("Temperature anomaly, K (rel. 1850–1900)")
ax.set_title("(a) HL vs. HL-CF temperature")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

# Right: attributable temperature difference
ax = axes[1]
if "HL" in w_temp_df["Scenario"].values and "HL-CF" in w_temp_df["Scenario"].values:
    d_hl  = w_temp_anom("HL")
    d_cf  = w_temp_anom("HL-CF")
    merged = d_hl[["Year","T_med"]].merge(d_cf[["Year","T_med"]], on="Year", suffixes=("_HL","_CF"))
    merged = merged[merged["Year"] >= 2000]
    diff = merged["T_med_HL"] - merged["T_med_CF"]
    ax.fill_between(merged["Year"], 0, diff, where=diff > 0,
                    color=SCEN_COLOR["HL"], alpha=0.4, label="HL additional warming")
    ax.fill_between(merged["Year"], 0, diff, where=diff < 0,
                    color="#2166ac", alpha=0.4, label="HL-CF additional warming")
    ax.plot(merged["Year"], diff, color=SCEN_COLOR["HL"], lw=2)
    ax.axhline(0, color="k", lw=0.8)

ax.axvline(EXT_START, color="#aaa", lw=1, ls=":", zorder=0)
ax.set_xlim(2000, 2300)
ax.set_xlabel("Year")
ax.set_ylabel("ΔT (HL − HL-CF), K")
ax.set_title("(b) Attributable temperature difference\n(= CO₂ pathway effect only; non-CO₂ identical)")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

pl.tight_layout()
save(fig, "F17_hl_attribution.png")

# %% [markdown]
# ### S02 — FLEX scenario space schematic

# %%
fig, ax = pl.subplots(figsize=(7, 5))

# Approximate positions of existing markers (warming, CDR reliance)
# CDR reliance: rough fraction of mitigation achieved by CDR (0=none, 1=all CDR)
marker_pos = {
    "VL":  (1.5, 0.5),
    "LN":  (1.6, 0.75),
    "L":   (2.0, 0.35),
    "ML":  (2.5, 0.25),
    "M":   (3.0, 0.10),
    "H":   (4.0, 0.05),
    "HL":  (2.5, 0.80),
}
# WIEMIP CF pairs
cf_pos = {
    "HL-CF": (2.0, 0.70),
    "ML-CF": (2.0, 0.35),
    "VL-CF": (1.7, 0.40),
}
# Illustrative space-spanning grid
for w in np.linspace(1.5, 4.0, 6):
    for cdr in np.linspace(0.1, 0.9, 5):
        ax.plot(w, cdr, ".", color="#ccc", ms=8, zorder=0)

for scen, (w, cdr) in marker_pos.items():
    ax.plot(w, cdr, "o", color=SCEN_COLOR[scen], ms=14, zorder=3)
    ax.text(w + 0.04, cdr + 0.02, scen, color=SCEN_COLOR[scen], fontsize=9, fontweight="bold")

for scen, (w, cdr) in cf_pos.items():
    src = scen.replace("-CF","")
    ax.plot(w, cdr, "s", color=SCEN_COLOR[src], ms=10, zorder=3, alpha=0.6)
    ax.text(w + 0.04, cdr + 0.02, scen, color=SCEN_COLOR[src], fontsize=8)
    # Arrow from source to CF
    src_pos = marker_pos[src]
    ax.annotate("", xy=(w, cdr), xytext=src_pos,
                arrowprops=dict(arrowstyle="->", color=SCEN_COLOR[src], lw=1.2, alpha=0.7))

ax.set_xlabel("End-of-21st-century warming level (°C)")
ax.set_ylabel("CDR reliance (fraction of total mitigation)")
ax.set_title("FLEX scenario space: existing markers (●), WIEMIP CFs (■),\nand illustrative space-spanning library (·)")
ax.set_xlim(1.2, 4.5)
ax.set_ylim(-0.05, 1.05)
ax.grid(alpha=0.2)
pl.tight_layout()
save(fig, "S02_flex_scenario_space.png")

# %% [markdown]
# ## Summary

# %%
print("\n" + "=" * 60)
print(f"All figures saved to: {PLOTS_DIR}")
print("=" * 60)
for f in sorted(PLOTS_DIR.glob("*.png")):
    print(f"  {f.name}")
