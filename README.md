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
├── data/                           # Input data (CSV files)
│   ├── history.csv                 # Historical emissions (global)
│   ├── history_regional.csv        # Historical emissions (regional)
│   ├── scenarios_complete_global.csv  # Pre-2100 scenarios (global)
│   └── scenarios_regional.csv      # Pre-2100 scenarios (regional)
├── notebooks/
│   └── 5191_extension.py          # Main extension notebook (jupytext format)
├── src/
│   └── extensions/                 # Extension functions
├── outputs/                        # Generated output files
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

2. Install dependencies with pixi:
   ```bash
   pixi install
   ```

### Running the Extension

1. Launch Jupyter Lab:
   ```bash
   pixi run notebook
   ```

2. Open and run `notebooks/5191_extension.py` (it will be displayed as a notebook thanks to jupytext)

Alternatively, run directly with Python:
```bash
pixi run python notebooks/5191_extension.py
```

## Input Data

The `data/` folder contains pre-processed CSV files:
- **scenarios_complete_global.csv**: Global marker scenarios (1750-2100)
- **history.csv**: Historical emissions for harmonization
- **scenarios_regional.csv**: Regional scenarios (1750-2100)
- **history_regional.csv**: Regional historical emissions

## Output Data

Generated files are saved to `outputs/`:
- **extended_scenarios_1750_2500.csv**: Final extended scenarios
- **continuous_emissions_timeseries_1750_2500.csv**: Continuous historical-future merge
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
