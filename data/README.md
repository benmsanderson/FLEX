# Data Directory

This directory contains input CSV files for the FLEX emissions scenarios project.

## Files tracked with Git LFS

All CSV files in this directory are tracked using **Git Large File Storage (LFS)** to handle their large size efficiently:

- `history_regional.csv` (~150 MB) - Historical regional emissions data
- `history.csv` (~165 KB) - Historical global emissions data  
- `scenarios_complete_global.csv` (~7.6 MB) - Complete global scenarios
- `scenarios_regional.csv` (~314 MB) - Regional scenario data

## Working with these files

### First-time setup

After cloning the repository, ensure Git LFS is installed and initialized:

```bash
# Install Git LFS (if not already installed)
# macOS: brew install git-lfs
# Ubuntu: sudo apt-get install git-lfs

# Initialize Git LFS
git lfs install

# Pull the LFS files
git lfs pull
```

### Checking LFS status

```bash
# List files tracked by LFS
git lfs ls-files

# Check LFS bandwidth/storage usage
git lfs env
```

### Updating data files

When updating these CSV files:

1. Simply modify or replace the files as normal
2. Git will automatically handle them through LFS when you commit
3. No special commands needed - `git add`, `git commit`, `git push` work as usual

## Output files

Output CSV files are generated in the `outputs/` directory and are **not tracked by Git** (excluded via `.gitignore`).
