# Quick Start Guide

## Step 1: Install Pixi

If you don't have Pixi installed:

**macOS/Linux**:
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

**Windows**:
```powershell
iwr -useb https://pixi.sh/install.ps1 | iex
```

## Step 2: Set Up Environment

```bash
cd /path/to/scenariomip-extensions
pixi install
```

This will create a `.pixi` directory with all dependencies.

## Step 3: Run the Extension

### Option A: Using Jupyter Lab (Recommended)

```bash
pixi run notebook
```

This opens Jupyter Lab. Then:
1. Navigate to `notebooks/5191_extension.py`
2. It will appear as a notebook (thanks to jupytext)
3. Run cells sequentially or "Run All"

### Option B: Direct Python Execution

```bash
pixi run python notebooks/5191_extension.py
```

This runs the entire notebook as a script.

## Step 4: Check Results

Output files are saved to the `outputs/` directory:

```bash
ls -lh outputs/
```

Key output files:
- `extended_scenarios_1750_2500.csv` - Main extended scenarios
- `continuous_emissions_timeseries_1750_2500.csv` - Historical + future
- `extensions_*.csv` - Per-model outputs

## Customization

### Change Parameters

Edit the parameters cell in the notebook:

```python
# %% tags=["parameters"]
make_plots: bool = False  # Set to True to generate diagnostic plots
dump_csvs: bool = True    # Set to False to skip intermediate CSV outputs
```

### Modify Storylines

The CO2 fossil fuel storylines are defined in the notebook:

```python
fossil_evolution_dictionary = {
    "VL": ["ECS", 2200, -3.5e3, 2450, 2500, 20, 20],
    "LN": ["ECS", 2120, -24e3, 2200, 2300, 20, 20],
    # ... etc
}
```

See the notebook comments for parameter definitions.

## Troubleshooting

### Import Errors

If you see import errors about `emissions_harmonization_historical`:
- Make sure you're in the project root directory
- The notebook adds `src/` to the Python path automatically

### Memory Issues

For large datasets, you may need to increase available memory:
- Close other applications
- Or process one scenario at a time

### CSV File Not Found

Ensure your CSV files are in the `data/` directory:
```bash
ls data/
# Should show:
# history.csv
# history_regional.csv
# scenarios_complete_global.csv
# scenarios_regional.csv
```

## Getting Help

1. Check the main [README.md](README.md) for methodology details
2. Review the [SETUP_SUMMARY.md](SETUP_SUMMARY.md) for technical setup info
3. Look at inline comments in the notebook for specific functions

## Development Mode

To make changes to the extension functions in `src/extensions/`:

1. Make your edits
2. Restart the notebook kernel to reload modules
3. Or use autoreload:
   ```python
   %load_ext autoreload
   %autoreload 2
   ```

## Version Control

The notebook is stored as a `.py` file using jupytext:
- Commit the `.py` file, not `.ipynb`
- Jupytext handles conversion automatically
- Changes are human-readable in git diffs
