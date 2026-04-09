# ScenarioMIP Extensions Methodology

This repository contains the methodology and code for extending ScenarioMIP marker scenarios from 2100 to 2500.

## Overview

The extension methodology takes CMIP7 ScenarioMIP marker scenarios (pre-2100) and extends them to 2500 using:
- Rule-based storylines for CO2 components (fossil, AFOLU, CDR)
- Sigmoid transitions for non-CO2 greenhouse gases
- Regional disaggregation maintaining 2100 composition ratios

## Repository Structure

```
.
├── configs/                        # YAML ensemble configurations
│   ├── scenariomip_default.yaml    # Standard 7-scenario ScenarioMIP setup
│   └── WIEMIP.yaml                 # 8-scenario setup with HL-CF counterfactual
├── data/                           # Input data (CSV files)
│   ├── history.csv                 # Historical emissions (global)
│   ├── history_regional.csv        # Historical emissions (regional)
│   ├── scenarios_complete_global.csv  # Pre-2100 scenarios (global)
│   └── scenarios_regional.csv      # Pre-2100 scenarios (regional)
├── notebooks/
│   ├── 5191_extension.py           # Build extended emissions scenarios
│   ├── 5195_optimise.py            # Optimise counterfactual scenario parameters
│   ├── 5195_optimise_parallel.py   # Parallel version of optimization (auto-selected)
│   ├── 5201_extension_fair_simulations.py  # Run FaIR climate simulations
│   └── 5202_extension_fair_plots.py        # Plot FaIR results
├── scripts/
│   ├── run_pipeline.py             # Papermill pipeline runner
│   └── ...
├── src/flex/                       # Library code
│   ├── config.py                   # YAML config loader (FlexConfig)
│   ├── optimise.py                 # Scenario optimisation via differential evolution
│   └── ...                         # Extension functions
├── outputs/                        # Generated output files (per-config)
├── pixi.toml                       # Pixi environment specification
└── README.md                       # This file
```

## Getting Started

### Prerequisites

- [Pixi](https://pixi.sh/) package manager

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd scenariomip-extensions
   ```

2. Install Git LFS (if not already installed):
   ```bash
   # macOS
   brew install git-lfs
   
   # Ubuntu/Debian
   sudo apt-get install git-lfs
   
   # Initialize Git LFS
   git lfs install
   ```

3. Pull large data files:
   ```bash
   git lfs pull
   ```

4. Install dependencies with pixi:
   ```bash
   pixi install
   ```

### Running the Extension

The pipeline is driven by YAML configuration files in `configs/`. Each config defines the set of scenarios, their storyline parameters, and optionally an optimisation step.

#### Automated pipeline (recommended)

Run the full pipeline for a given configuration:
```bash
pixi run pipeline scenariomip_default   # standard 7-scenario run
pixi run pipeline WIEMIP                # includes HL-CF optimisation step
```

Resume from a specific step (skips earlier steps):
```bash
pixi run pipeline WIEMIP -- --from 5201   # resume from FaIR simulations
pixi run pipeline WIEMIP --   # re-run just the plots
```

**Parallel optimization** *(for configs with multiple optimization targets)*:
```bash
# Run optimization scenarios in parallel (auto-detects cores, capped at 20)
pixi run pipeline WIEMIP -- --parallel -1

# Or specify number of parallel jobs
pixi run pipeline WIEMIP -- --parallel 3

# Override the 20-worker cap if needed
pixi run pipeline WIEMIP -- --parallel 30
```

For configs like WIEMIP with multiple optimization targets (e.g., HL-CF, ML-CF, VL-CF), parallel mode runs them simultaneously. This exploits cluster resources effectively:
- Use `--parallel -1` to auto-detect CPU cores (capped at 20 workers for safety)
- Use `--parallel N` where N ≤ 20 to specify exact number of workers
- Use `--parallel N` where N > 20 to explicitly override the cap
- Each optimization already uses vectorized differential evolution internally

This executes notebooks in sequence via [papermill](https://papermill.readthedocs.io/):

1. **5191_extension** — Build extended emissions scenarios (1750–2500)
2. **5195_optimise** *(only if the config defines an `optimization` section)* — Optimise counterfactual scenario parameters against FaIR temperature targets
3. **5201_extension_fair_simulations** — Run FaIR v2.2 climate simulations on all scenarios
4. **5202_extension_fair_plots** — Generate diagnostic plots

Rendered output notebooks are saved to `outputs/<config_name>/notebooks/`.

#### Interactive use

You can also run notebooks interactively in Jupyter Lab:
```bash
pixi run notebook
```

Each notebook has a `config_name` parameter cell (tagged `parameters` for papermill). Change the value to switch configurations:
```python
# %% tags=["parameters"]
config_name = "WIEMIP"     # or "scenariomip_default"
```

### Configuration

Configs live in `configs/<name>.yaml` and specify:
- **scenario_model_match** — mapping of marker names to (scenario, model) pairs
- **storylines** — CO2 storyline parameters per scenario
- **non_co2** — sigmoid targets for non-CO2 species
- **optimization** *(optional)* — parameters to optimise via `scipy.optimize.differential_evolution`, including bounds, fixed parameters, and FaIR temperature targets

When no `optimization` section is present, the pipeline skips `5195_optimise`.

See `configs/scenariomip_default.yaml` for a minimal example and `configs/WIEMIP.yaml` for a config with optimisation.

## Input Data

The `data/` folder contains pre-processed CSV files (~488 MB total, managed by Git LFS):
- **scenarios_complete_global.csv** (8 MB): Global marker scenarios (1750-2100)
- **history.csv** (192 KB): Historical emissions for harmonization
- **scenarios_regional.csv** (320 MB): Regional scenarios (1750-2100)
- **history_regional.csv** (160 MB): Regional historical emissions

**Note**: These files are tracked with Git Large File Storage (Git LFS). Make sure you've run `git lfs pull` after cloning to download them. See [data/README.md](data/README.md) for more details on working with these files.

## Output Data

Generated files are saved to `outputs/<config_name>/`:
- **emissions_1750-2500.csv**: Extended emissions for all scenarios
- **continuous_emissions_timeseries_1750_2500.csv**: Continuous historical-future merge
- **fair_output_*.csv**: FaIR simulation results (temperature, forcing, concentrations, etc.)
- **notebooks/**: Rendered pipeline notebooks with full outputs
- **plots/**: Diagnostic plots from FaIR results
- Per-model CSV files for individual scenarios

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

[Add citation information when published]

## License

[Add license information]

## Contact

Benjamin Sanderson
