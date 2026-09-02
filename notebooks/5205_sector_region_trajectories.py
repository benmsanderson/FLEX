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
# # Sectoral Regional Emissions Trajectories
#
# Generates one figure per scenario from
# `extensions_full_emissions_timeseries_2023_2500.csv`, with one panel per
# emission sub-sector and one line per region in each panel.

# %% tags=["parameters"]
config_name = "scenariomip_default"
species = "OC"
year_min = 2050
year_max = 2300
ncols = 3
max_legend_entries = 20

# %% [markdown]
# ## Setup

# %%
from math import ceil

import matplotlib.pyplot as pl
import numpy as np
import pandas as pd
from pathlib import Path

from flex.config import DATA_DIR, load_config

cfg = load_config(config_name)

OUTPUTS_DIR = cfg.outputs_dir
PROJECT_ROOT = DATA_DIR.parent
PLOTS_DIR = PROJECT_ROOT / "outputs" / "presentation" / "sector_region_trajectories"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Scenariomip outputs: {OUTPUTS_DIR}")
print(f"Saving figures to:   {PLOTS_DIR}")


# %%
_smm_raw = cfg.scenario_model_match
SCENARIO_META = {k: {"scenario": v[0], "model": v[1], "color": v[2]} for k, v in _smm_raw.items()}
SCEN_COLOR = {k: v["color"] for k, v in SCENARIO_META.items()}
SCEN_LABELS = list(SCENARIO_META.keys())

SCEN_COLOR["LN"] = "#0097a0"
SCEN_COLOR["ML"] = "#907000"
SCEN_COLOR["HL"] = "#8a10a8"

pl.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 12,
    "axes.titlesize": 12,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


# %%
def year_columns(df):
    return [c for c in df.columns if str(c).replace(".", "").isdigit()]


def species_variable_prefix(species_name):
    return f"Emissions|{species_name}"


def get_species_subsector_variables(df, species_name):
    prefix = species_variable_prefix(species_name) + "|"
    variables = sorted(v for v in df["variable"].dropna().unique() if isinstance(v, str) and v.startswith(prefix))
    return variables


def format_subsector_label(variable, species_name):
    prefix = species_variable_prefix(species_name) + "|"
    if variable.startswith(prefix):
        return variable[len(prefix):]
    return variable


def sanitize_name(text):
    return text.replace("|", "_").replace("/", "_").replace(" ", "_")


def build_region_colors(regions):
    cmap = pl.get_cmap("tab20")
    ordered = sorted(regions)
    if not ordered:
        return {}
    return {region: cmap(idx % cmap.N) for idx, region in enumerate(ordered)}


def save(fig, name):
    path = PLOTS_DIR / name
    fig.savefig(path)
    print(f"  Saved {path.name}")
    pl.close(fig)


def get_legend_layout(n_labels):
    ncols_legend = min(5, n_labels)
    nrows_legend = ceil(n_labels / ncols_legend)
    bottom_margin = min(0.15, 0.025 + 0.03 * nrows_legend)
    return ncols_legend, bottom_margin


# %%
ext_df = pd.read_csv(OUTPUTS_DIR / "extensions_full_emissions_timeseries_2023_2500.csv")
YEAR_COLS = year_columns(ext_df)
YEAR_VALUES = np.array([int(float(c)) for c in YEAR_COLS])

species_variables = get_species_subsector_variables(ext_df, species)
if not species_variables:
    available_species = sorted({
        v.split("|")[1]
        for v in ext_df["variable"].dropna().unique()
        if isinstance(v, str) and v.startswith("Emissions|") and v.count("|") >= 2
    })
    raise ValueError(
        f"No sub-sector variables found for species '{species}'. "
        f"Try one of: {available_species[:20]}"
    )

print(f"Found {len(species_variables)} sub-sector variables for {species}:")
for variable in species_variables:
    print(f"  - {variable}")


# %%
def plot_scenario_figure(scen_label):
    scen_name = SCENARIO_META[scen_label]["scenario"]
    scen_df = ext_df[ext_df["scenario"] == scen_name].copy()
    if scen_df.empty:
        print(f"Skipping {scen_label}: no rows found for scenario '{scen_name}'")
        return

    n_panels = len(species_variables)
    nrows = ceil(n_panels / ncols)
    fig, axes = pl.subplots(nrows, ncols, figsize=(5.2 * ncols, 3.6 * nrows), sharex=True)
    axes = np.atleast_1d(axes).ravel()

    scen_regions = sorted(
        scen_df[scen_df["variable"].isin(species_variables)]["region"].dropna().unique()
    )
    region_colors = build_region_colors(scen_regions)

    legend_handles = None
    legend_labels = None

    for ax, variable in zip(axes, species_variables):
        subset = scen_df[scen_df["variable"] == variable].copy()
        if subset.empty:
            ax.set_visible(False)
            continue

        unit_values = subset["unit"].dropna().unique()
        unit_label = unit_values[0] if len(unit_values) else ""

        for _, row in subset.sort_values("region").iterrows():
            region = row["region"]
            values = row[YEAR_COLS].to_numpy(dtype=float)
            year_mask = (YEAR_VALUES >= year_min) & (YEAR_VALUES <= year_max)
            ax.plot(
                YEAR_VALUES[year_mask],
                values[year_mask],
                lw=1.4,
                alpha=0.95,
                color=region_colors.get(region),
                label=region,
            )

        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

        ax.axhline(0, color="#777777", lw=0.7, ls=":", zorder=0)
        ax.grid(alpha=0.25)
        ax.set_title(format_subsector_label(variable, species), fontsize=13)
        ax.set_xlim(year_min, year_max)
        ax.set_ylabel(unit_label, fontsize=12)

    for ax in axes[n_panels:]:
        ax.set_visible(False)

    for ax in axes[-ncols:]:
        if ax.get_visible():
            ax.set_xlabel("Year", fontsize=12)

    if legend_handles and legend_labels:
        shown_labels = legend_labels
        shown_handles = legend_handles
        if len(legend_labels) > max_legend_entries:
            shown_labels = legend_labels[:max_legend_entries]
            shown_handles = legend_handles[:max_legend_entries]

        legend_ncols, bottom_margin = get_legend_layout(len(shown_labels))
        fig.legend(
            shown_handles,
            shown_labels,
            loc="lower center",
            ncol=legend_ncols,
            frameon=False,
            bbox_to_anchor=(0.5, 0.01),
            fontsize=10,
        )
    else:
        bottom_margin = 0.04

    fig.suptitle(f"{scen_label}: {species} regional sub-sector emissions", y=1.02, fontsize=16)
    fig.tight_layout(rect=(0, bottom_margin, 1, 0.98))

    save(fig, f"sector_region_trajectories_{sanitize_name(species)}_{scen_label}.png")


# %%
for scenario_label in SCEN_LABELS:
    plot_scenario_figure(scenario_label)

print("Done.")