#!/usr/bin/env python
"""
Parallel optimization script for FLEX.

Run multiple scenario optimizations in parallel using joblib.
Designed for HPC/cluster environments.

Usage:
    python run_optimization_parallel.py [config_name] [--n-jobs N]

Example:
    python run_optimization_parallel.py WIEMIP --n-jobs 4
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from flex.config import load_config
from flex.optimise import optimize_scenario, modify_emissions_csv


def optimize_single_marker(marker, cfg, base_emissions_csv, verbose=True):
    """Wrapper function for parallel execution."""
    if verbose:
        print(f"\n{'='*60}")
        print(f"[PARALLEL] Starting optimization: {marker}")
        print(f"{'='*60}")
    
    result = optimize_scenario(
        cfg,
        marker=marker,
        base_emissions_csv=base_emissions_csv,
        memory_limited=True,
    )
    
    if verbose:
        print(f"\n[PARALLEL] Completed {marker}:")
        print(f"  exp_targ  = {result['exp_targ']:.1f} Mt CO2/yr (total CO2)")
        print(f"  sig_start = {result['sig_start']:.0f}")
        print(f"  sig_end   = {result['sig_end']:.0f}")
        print(f"  Target T  = {result['target_temp']:.4f} K")
        print(f"  Departure = {result['departure_year']}")
        print(f"  Final cost = {result['final_cost']:.6f}")
    
    return marker, result


def write_optimized_scenario(marker, result, cfg, current_csv, output_dir):
    """Write optimized scenario to emissions CSV."""
    departure_year = result["departure_year"]
    
    # Find source marker
    source_marker = None
    base_scenario = cfg.scenario_model_match[marker][0]
    for m, info in cfg.scenario_model_match.items():
        if m != marker and info[0] == base_scenario and info[1] == cfg.scenario_model_match[marker][1]:
            source_marker = m
            break
    
    if source_marker is None:
        raise ValueError(f"No source marker found for {marker}")
    
    # Read emissions
    df_emis = pd.read_csv(current_csv)
    source_ffi = df_emis[(df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 FFI")]
    source_afolu = df_emis[(df_emis["scenario"] == source_marker) & (df_emis["variable"] == "CO2 AFOLU")]
    year_cols = [c for c in df_emis.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    co2_ffi = source_ffi[year_cols].values.flatten().copy()
    co2_afolu = source_afolu[year_cols].values.flatten().copy() if len(source_afolu) else np.zeros_like(co2_ffi)

    # Build trajectory
    dep_idx_emis = np.searchsorted(years, departure_year + 0.5)
    exp_targ = result["exp_targ"]
    sig_start = result["sig_start"]
    sig_end = result["sig_end"]
    exp_end = int(sig_start)

    total_co2 = (co2_ffi + co2_afolu).copy()
    dep_value = total_co2[dep_idx_emis]

    for i in range(dep_idx_emis, len(total_co2)):
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            frac = (years[i] - departure_year) / yr_total
            total_co2[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            total_co2[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3
            total_co2[i] = exp_targ * (1 - s)
        else:
            total_co2[i] = 0.0

    co2_opt = co2_ffi.copy()
    co2_opt[dep_idx_emis:] = total_co2[dep_idx_emis:] - co2_afolu[dep_idx_emis:]

    # Write
    output_path = str(output_dir / "emissions_1750-2500.csv")
    modify_emissions_csv(
        current_csv, source_marker, marker,
        co2_ffi_trajectory=co2_opt,
        departure_year=departure_year,
        output_path=output_path,
    )
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Run FLEX optimization in parallel",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "config_name",
        default="WIEMIP",
        nargs="?",
        help="Configuration name (YAML file in configs/)"
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs (-1 for all cores, capped at 20 unless explicitly overridden)"
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=10,
        help="Verbosity level for joblib (0-50)"
    )
    
    args = parser.parse_args()
    
    # Load config
    cfg = load_config(args.config_name)
    OUTPUTS_DIR = cfg.outputs_dir
    
    # Cap n_jobs at 20 when using -1, but allow explicit overrides
    import os
    if args.n_jobs == -1:
        n_jobs_effective = min(os.cpu_count() or 1, 20)
        cap_msg = f" (auto-detected {os.cpu_count()}, capped at 20)"
    else:
        n_jobs_effective = args.n_jobs
        cap_msg = f" (explicit override)" if args.n_jobs > 20 else ""
    
    print(f"{'='*80}")
    print(f"FLEX Parallel Optimization")
    print(f"{'='*80}")
    print(f"Config: {cfg.name}")
    print(f"Scenarios: {list(cfg.scenario_model_match.keys())}")
    print(f"Optimization targets: {list(cfg.optimization.keys())}")
    print(f"Parallel jobs: {n_jobs_effective}{cap_msg}")
    print(f"{'='*80}\n")
    
    # Locate base emissions CSV
    base_emissions_csv = str(OUTPUTS_DIR / "emissions_1750-2500.csv")
    if not Path(base_emissions_csv).exists():
        raise FileNotFoundError(
            f"Pipeline-generated emissions not found: {base_emissions_csv}\n"
            "Run 5191 first."
        )
    print(f"Base emissions: {base_emissions_csv}")
    
    df_check = pd.read_csv(base_emissions_csv, usecols=["scenario", "variable"])
    print(f"Scenarios in CSV: {sorted(df_check['scenario'].unique())}\n")
    
    # Collect markers to optimize
    markers_to_optimize = []
    for marker, opt_settings in cfg.optimization.items():
        if opt_settings.get("enabled", True):
            markers_to_optimize.append(marker)
        else:
            print(f"Skipping {marker} (disabled)")
    
    print(f"\nWill optimize {len(markers_to_optimize)} markers in parallel: {markers_to_optimize}\n")
    
    # Run optimizations in parallel
    print(f"Starting parallel optimization...")
    parallel_results = Parallel(n_jobs=n_jobs_effective, verbose=args.verbose)(
        delayed(optimize_single_marker)(marker, cfg, base_emissions_csv, verbose=True)
        for marker in markers_to_optimize
    )
    
    # Convert to dictionary
    opt_results = {marker: result for marker, result in parallel_results}
    
    print(f"\n{'='*60}")
    print(f"All {len(opt_results)} optimizations complete!")
    print(f"{'='*60}\n")
    
    # Write optimized scenarios to CSV sequentially
    # (must be sequential to avoid race conditions when modifying the same file)
    current_csv = base_emissions_csv
    for marker in markers_to_optimize:
        result = opt_results[marker]
        print(f"Writing optimized scenario: {marker}")
        current_csv = write_optimized_scenario(marker, result, cfg, current_csv, OUTPUTS_DIR)
    
    print(f"\nAll scenarios written to: {current_csv}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*80}")
    summary_data = []
    for marker, result in opt_results.items():
        summary_data.append({
            'Marker': marker,
            'Departure': result['departure_year'],
            'Target T (K)': f"{result['target_temp']:.4f}",
            'exp_targ': f"{result['exp_targ']:.0f}",
            'sig_start': f"{result['sig_start']:.0f}",
            'sig_end': f"{result['sig_end']:.0f}",
            'Cost': f"{result['final_cost']:.6f}",
            'Success': result['success'],
        })
    
    df_summary = pd.DataFrame(summary_data)
    print(df_summary.to_string(index=False))
    print(f"{'='*80}\n")
    
    # Save summary to file
    summary_file = OUTPUTS_DIR / "optimization_summary.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
