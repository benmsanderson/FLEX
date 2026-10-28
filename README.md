# FLEX: ScenarioMIP Extensions

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23736599.svg)](https://doi.org/10.5281/zenodo.23736599)

This repository contains the methodology and code for extending ScenarioMIP marker scenarios from 2100 to 2500.

## Overview

The extension methodology takes CMIP7 ScenarioMIP marker scenarios (pre-2100) and extends them to 2500 using:
- Rule-based storylines for CO2 components (fossil, AFOLU, CDR)
- Sigmoid transitions for non-CO2 greenhouse gases
- Regional disaggregation maintaining 2100 composition ratios

FLEX is a standalone copy of the extension step (`notebooks/5191_extension.py`)
of the CMIP7 emissions harmonization pipeline,
[iiasa/emissions_harmonization_historical](https://github.com/iiasa/emissions_harmonization_historical).
Given the same inputs it reproduces that pipeline's extended emissions; see
[Reproducing the harmonization pipeline](#reproducing-the-harmonization-pipeline).

## Repository Structure

```
.
├── data/                           # Inputs; see data/README.md
│   ├── history.csv                 # Historical emissions, global (Git LFS)
│   └── history_regional.csv        # Historical emissions, regional (Git LFS)
├── notebooks/
│   └── 5191_extension.py           # Main extension notebook (jupytext format)
├── scripts/
│   ├── fetch_data.py               # Check inputs are present and which release they are
│   └── convert_scenario_release.py # Convert the public v0.2 spreadsheet to CSV
├── src/
│   └── flex/                       # Extension functions
├── tests/regression/               # Comparison against the harmonization pipeline
├── outputs/                        # Generated output files (not tracked)
├── pixi.toml                       # Pixi environment specification
└── README.md                       # This file
```

The scenario inputs, `data/scenarios_complete_global.csv` and
`data/scenarios_regional.csv`, are not distributed with FLEX; see
[Input Data](#input-data).

## Getting Started

### Prerequisites

- [Pixi](https://pixi.sh/) package manager
- [Git LFS](https://git-lfs.com/), for the historical emissions files

### Installation

1. Clone this repository and pull the historical data:
   ```bash
   git clone https://github.com/benmsanderson/FLEX.git
   cd FLEX
   git lfs install
   git lfs pull
   ```

2. Install dependencies with pixi:
   ```bash
   pixi install
   ```

3. Put the scenario files in `data/` (or in `$FLEX_DATA_DIR`) and check them:
   ```bash
   pixi run python scripts/fetch_data.py
   ```

### Running the Extension

Run the notebook as a script from the repository root:
```bash
pixi run python notebooks/5191_extension.py
```

or open `notebooks/5191_extension.py` in Jupyter Lab (`pixi run notebook`);
jupytext displays it as a notebook. Intermediate CSVs
(`first_draft_extended_*.csv`, `co2_fossil_fuel_extenstions_*.csv`) are written
to the working directory.

## Input Data

| File | Contents | Source |
|------|----------|--------|
| `scenarios_complete_global.csv` | Harmonised and infilled marker scenarios, World, 2023-2100 | ScenarioMIP release, obtain separately |
| `scenarios_regional.csv` | Harmonised marker scenarios, IAM regions | Regional delivery, obtain separately |
| `history.csv` | Historical emissions, global | Included (Git LFS) |
| `history_regional.csv` | Historical emissions, regional | Included (Git LFS) |

The ScenarioMIP marker scenarios carry IIASA's terms and are not redistributed
here. The open v0.2 release
([10.5281/zenodo.19825038](https://doi.org/10.5281/zenodo.19825038)) provides the
global file via `scripts/convert_scenario_release.py`, but has no regional
breakdown. See [data/README.md](data/README.md) for where to get each file, its
licence and required attribution.

Set `FLEX_DATA_DIR` to read inputs from a directory outside the repository.

## Output Data

Generated files are saved to `outputs/`:
- **extended_scenarios_1750_2500.csv**: Final extended scenarios, global
- **continuous_emissions_timeseries_1750_2500.csv**: Continuous historical-future merge
- **extensions_full_emissions_timeseries_2023_2500.csv**: Extended scenarios, all regions
- **scenarios_complete_global_1750_2100.csv**: Input scenarios glued to history
- **extensions_<model>.csv**: Per-model extended scenarios

## Reproducing the harmonization pipeline

The code in `src/flex` is the `extensions` package of
emissions_harmonization_historical, and `notebooks/5191_extension.py` is that
repository's `notebooks/5191_extension.py` with database access replaced by CSV
files and plotting removed. The two produce the same numbers.

To check this, run `5191_extension.py` in both repositories on the same inputs,
then:

```bash
EM_HARM_DIR=/path/to/emissions_harmonization_historical pixi run test
```

This compares `continuous_emissions_timeseries_1750_2500.csv` and
`extensions_full_emissions_timeseries_2023_2500.csv` from both runs (rtol 1e-5,
atol 1e-6). `EM_HARM_DIR` defaults to a sibling checkout; the tests are skipped
if either set of outputs is missing.

## Extension Methodology

### CO2 Components

Three storyline types control CO2 evolution:

1. **CS (Constant-Sigmoid)**: Hold constant, then smooth transition to zero
2. **ECS (Exponential-Constant-Sigmoid)**: Initial trend, plateau, then transition
3. **CSCS (Constant-Sigmoid-Constant-Sigmoid)**: Two-phase transition

### Non-CO2 Gases

- Sigmoid transitions to specified 2500 targets
- Species-specific endpoints for CH4, Sulfur, etc.
- Regional composition maintained from 2100 ratios

### CDR Disaggregation

- BECCS, DACCS, Ocean, Enhanced Weathering, Biochar, Soil Management
- Maintain 2100 technology ratios through extensions
- Two strategies: NEG (gross positive decays) and POS (CDR constant)

## Development

The repository uses:
- **Pixi** for environment management
- **Jupytext** for version-controlling notebooks as `.py` files
- **Git** for version control (notebooks as percent format)

## Citation

If you use FLEX, please cite the description paper:

> Sandstad, M., Sanderson, B., Chini, L., Friedlingstein, P., Kikstra, J.,
> Ziehn, T., Zecchetto, M., Högner, A., Nicholls, Z., Yokohata, T., King, A.,
> Smith, C., and Séférian, R. (2026). *FLEX: ScenarioMIP CMIP7 Post-2100
> Extensions Framework*. Zenodo. https://doi.org/10.5281/zenodo.22212710

Submitted to *Environmental Research Letters*. The DOI above is the concept DOI
and always resolves to the most recent version.

Please also cite the software version you ran. For v1.0.0:

> Sandstad, M. and Sanderson, B. M. (2026). *FLEX: ScenarioMIP CMIP7 Post-2100
> Extensions Framework (software)*, v1.0.0. Zenodo.
> https://doi.org/10.5281/zenodo.23736600

Every release is archived on Zenodo under the concept DOI
[10.5281/zenodo.23736599](https://doi.org/10.5281/zenodo.23736599), which
resolves to the latest version. `CITATION.cff` has the details, and GitHub's
"Cite this repository" button formats them.

## License

The source code in this repository is released under the MIT Licence (see
`LICENSE`).

That does **not** extend to the datasets under `data/`. The historical emissions
files are CC-BY 4.0 and derive from CEDS and the Global Carbon Budget; the
ScenarioMIP marker scenarios must be obtained separately and carry IIASA's terms.
See [data/README.md](data/README.md) for the source, licence and required
attribution of every input.

## Contact

Marit Sandstad and Benjamin Sanderson, CICERO Center for International Climate
Research, Oslo.
