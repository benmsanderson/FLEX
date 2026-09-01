# Input data

The scenario files this pipeline reads are **not** stored in this repository:
they are a third-party dataset that FLEX has no right to redistribute. The
historical files *are* kept here, under the terms in the attribution section
below. Fetch what is missing before a first run, then verify everything with:

```bash
pixi run python scripts/fetch_data.py
```

## ScenarioMIP marker scenarios — you must obtain these

`data/scenarios_complete_global.csv`, `data/scenarios_regional.csv`

Download from the ScenarioMIP Explorer hosted by IIASA:

- Portal: <https://scenariomip.apps.ece.iiasa.ac.at>
- Current release (open access): **v0.2**,
  [10.5281/zenodo.19825038](https://doi.org/10.5281/zenodo.19825038) —
  `ScenarioMIP_emissions_marker_scenarios_v0.2.xlsx`

Convert it to the CSV this pipeline reads:

```bash
pixi run python scripts/convert_scenario_release.py \
    ScenarioMIP_emissions_marker_scenarios_v0.2.xlsx
```

That writes `data/scenarios_complete_global.csv`. The script strips the
`Climate Assessment|Harmonized and Infilled|` prefix the release puts on every
series, renames scenarios to the names the configs use (mapping via the model
column, which is identical in both), and trims the year columns to 2023 onward.
The result has the same 364 rows, 52 variables and 2023-2100 columns as the
delivery the pipeline was built on.

Two things to know before you run:

1. **v0.2 is not identical to the v0.1 delivery this pipeline was built on**
   ([10.5281/zenodo.18497404](https://doi.org/10.5281/zenodo.18497404), now
   access-restricted). Comparing the converted v0.2 against v0.1: 342 of 364
   series are byte-identical. The revisions fall in Low, Medium-to-Low,
   Low-to-Negative and Medium — chiefly `Emissions|CO2|Energy and Industrial
   Processes`, `Emissions|CO2|AFOLU` and some ozone precursors — with a largest
   single change of about 716 Mt CO2/yr. Very Low, High and High-to-Low are
   unchanged. Expect published output to shift accordingly for the four affected
   markers.
2. **There is no regional data in the published release.** The spreadsheet is
   World-only, so `data/scenarios_regional.csv` cannot be built from it. Global
   workflows run from the open release; anything needing the regional or
   gridded breakdown requires the regional delivery, requested through the
   portal above.

Expected layout: IAMC wide format, index columns
`model, scenario, region, variable, unit`, one column per year.

## Historical emissions — included in this repository

`data/history.csv`, `data/history_regional.csv` (Git LFS)

These are retained here for convenience and are redistributable, but they are
**not** FLEX's work and are **not** covered by this repository's MIT licence.

- Produced by the CMIP7 emissions harmonization pipeline,
  <https://github.com/iiasa/emissions_harmonization_historical>
- Underlying sources, both **CC-BY 4.0**:
  - **CEDS** — Hoesly et al. (2018), *Historical (1750–2014) anthropogenic
    emissions of reactive gases and aerosols from the Community Emissions Data
    System*, Geosci. Model Dev. 11, 369–408.
    <https://doi.org/10.5194/gmd-11-369-2018>
  - **Global Carbon Budget** — Friedlingstein et al., Earth Syst. Sci. Data.
    <https://doi.org/10.5194/essd-16-2625-2024>

If you use these series, cite the sources above rather than FLEX.

## Bespoke scenario deliveries — not included

`data/vl-extensions-inputs/`

Purpose-built deliveries supplied directly by the scenario providers for the
`vl-frankenstein` configuration. Pre-release material, not redistributable;
request them from the providers. Every other configuration runs without them.

## FaIR inputs — fetched automatically

`data/fair-inputs/`

FaIR calibrated-constrained parameters,
[10.5281/zenodo.7112539](https://doi.org/10.5281/zenodo.7112539). Downloaded on
demand by `notebooks/5201_extension_fair_simulations.py` and by
`scripts/fetch_data.py`.

## If you already have a working copy of the data

The scenario files used to be tracked here. When you pull the commit that
removes them, **git deletes them from your working tree** — adding them to
`.gitignore` does not prevent this, because `.gitignore` only applies to files
git is not already tracking. `data/history.csv` and `data/fair-inputs/` are
unaffected; they are still tracked.

Before pulling, copy them somewhere safe:

```bash
mkdir -p ~/flex-data
cp -a data/. ~/flex-data/
git pull
```

Then either copy the scenario files back into `data/` — they are gitignored now,
so nothing will disturb them again on that branch — or, better, leave them
outside the repository and point FLEX at them:

```bash
export FLEX_DATA_DIR=~/flex-data
```

`FLEX_DATA_DIR` overrides the default `<repo>/data` for every input the pipeline
reads. The directory has to hold everything `data/` would, so copy the whole
directory as above rather than just the scenario files.

The second option is worth preferring. History is unchanged, so any pre-removal
commit still tracks the scenario files: checking one out will overwrite whatever
is in `data/`, and checking back out will delete it again. Keeping your inputs
outside the working tree makes branch switching harmless.

## Licensing summary

The MIT licence in this repository covers the **source code only**. It does not
cover any dataset in this directory. Each dataset keeps the terms of its own
source, listed above, and outputs derived from them inherit those attribution
requirements.

## Reproducibility

`scripts/fetch_data.py` carries the SHA-256 each input had when the pipeline was
developed. Hashes are not data, so recording them costs nothing in licensing
terms while letting you confirm byte-identical inputs. A mismatch usually means
a different upstream release rather than a fault — the script names which branch
each known hash belongs to.
