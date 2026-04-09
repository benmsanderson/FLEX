# Parallel Optimization Guide

## Overview

We've integrated parallel optimization into your existing pixi/papermill workflow. The optimization runs 3 independent scenarios (HL-CF, ML-CF, VL-CF) that can be computed simultaneously on your cluster.

## Integration with Existing Workflow

The parallel optimization is **seamlessly integrated** into your existing pipeline command. Simply add the `--parallel` flag:

### Standard Sequential Run (Original)
```bash
pixi run pipeline WIEMIP
```

### Parallel Run (New!)
```bash
# Use all available CPU cores (capped at 20 for safety)
pixi run pipeline WIEMIP -- --parallel -1

# Use specific number of cores (recommended: 3 for 3 scenarios)
pixi run pipeline WIEMIP -- --parallel 3

# Override the 20-worker cap if you have a large cluster
pixi run pipeline WIEMIP -- --parallel 50
```

**Note:** The `--` is required to pass arguments through pixi to the underlying script.

### Worker Cap Behavior

- `--parallel -1`: Auto-detects cores but **caps at 20 workers** (prevents accidental resource overuse)
- `--parallel N` (N ≤ 20): Uses exactly N workers
- `--parallel N` (N > 20): Explicitly overrides the cap and uses N workers

## How It Works

1. **Automatic Selection**: When you use `--parallel N` (where N ≠ 1), the pipeline automatically uses `5195_optimise_parallel.py` instead of `5195_optimise.py`

2. **Parameter Injection**: Papermill injects both `config_name` and `n_jobs` parameters into the parallel notebook

3. **Transparent Execution**: The output notebook is still saved as `5195_optimise.ipynb` (same name as sequential), maintaining consistency in your outputs

4. **Full Pipeline**: All other steps (5191, 5201, 5202) run normally—only the optimization step is parallelized

## Complete Workflow Examples

### Full Pipeline with Parallel Optimization
```bash
# Run entire pipeline from scratch with parallelization
pixi run pipeline WIEMIP -- --parallel 3
```

### Resume from Optimization Step
```bash
# Re-run just the optimization in parallel
pixi run pipeline WIEMIP -- --from 5195 --parallel 3
```

### Run Only Optimization Step
```bash
# Useful for testing optimization parameters
pixi run pipeline WIEMIP -- --only 5195 --parallel -1
```

## Performance Benefits

- **Sequential (original)**: Runs 3 optimizations one after another (~3x time)
- **Parallel (new)**: Runs all 3 optimizations simultaneously
- Each optimization uses differential evolution which is already vectorized internally

## Cluster Considerations

### Resource Allocation

Since you're on a cluster, be mindful of:

1. **CPU cores**: Each optimization task is CPU-bound. 
   - `-1` auto-detects cores but caps at 20 workers for safety
   - Use explicit numbers to override: `--parallel 30` for 30 workers
   - For WIEMIP (3 scenarios), `--parallel 3` is optimal

2. **Memory**: Each FaIR run needs memory. The code uses `memory_limited=True` which uses a 5-member ensemble instead of ~1000 members.

3. **I/O contention**: Multiple processes write temporary files. This is handled safely.

### Slurm Job Example

If using Slurm on your cluster:

```bash
#!/bin/bash
#SBATCH --job-name=flex_pipeline
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00

cd /div/no-backup-nac/users/bensan/FLEX

# Load pixi environment and run pipeline
pixi run pipeline WIEMIP -- --parallel 3
```

## Files Created/Modified

### New Files
- `notebooks/5195_optimise_parallel.py` - Parallel version of optimization notebook
- `scripts/run_optimization_parallel.py` - Standalone script (alternative to pipeline)

### Modified Files
- `scripts/run_pipeline.py` - Added `--parallel` flag and automatic notebook selection
- `README.md` - Updated documentation

## Existing Parallel Optimization Levels

Your code already has **nested parallelization**:

### Level 1: Scenario-Level (NEW - What we added)
- 3 independent scenarios run simultaneously
- Controlled by `--parallel N` flag

### Level 2: Vectorized Differential Evolution (EXISTING)
- Within each scenario, differential evolution evaluates **multiple candidates in ONE FaIR run**
- Default: `popsize=5` candidates per iteration
- This is why you see `vectorized=True` in the code

### Level 3: FaIR Ensemble (MINIMAL during optimization)
- FaIR can run multiple climate configs
- During optimization: `n_configs=1` for speed
- During verification: full ensemble

## Alternative: Standalone Script

If you prefer not to use the pipeline, you can run optimization directly:

```bash
cd /div/no-backup-nac/users/bensan/FLEX
pixi run python scripts/run_optimization_parallel.py WIEMIP --n-jobs 3
```

This runs **only** the optimization step (not the full pipeline).

## Output

The parallel version produces identical output to the sequential version:
- Optimized parameters for each scenario
- Updated `emissions_1750-2500.csv` with counterfactual scenarios
- Verification plots comparing optimized vs. source scenarios
- `optimization_summary.csv` with results table

## Monitoring

Watch CPU usage during optimization:
```bash
htop  # or top
```

You should see multiple Python processes running (one per job) during the parallel optimization phase.

## Troubleshooting

**Q: I get "no such file" errors**  
A: Make sure you're in the FLEX directory: `cd /div/no-backup-nac/users/bensan/FLEX`

**Q: Optimization is still slow**  
A: Each scenario's optimization is inherently CPU-intensive. The parallelization only helps when you have multiple scenarios. Each scenario still takes time proportional to `maxiter × popsize × n_configs`.

**Q: Can I increase n_configs during optimization?**  
A: Yes, edit `configs/WIEMIP.yaml` and change `n_configs: 1` to a higher value, but expect slower optimization.
