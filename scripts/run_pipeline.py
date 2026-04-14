"""Run the FLEX notebook pipeline for a given config via papermill."""

import argparse
import sys
import jupytext
from pathlib import Path

import papermill as pm

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"

ALL_STEPS = [
    "5191_extension",
    "5195_optimise",
    "5196_apply_optimised",
    "5201_extension_fair_simulations",
    "5202_extension_fair_plots",
]


def run_notebook(notebook_name: str, config_name: str, output_dir: Path, n_jobs: int = 1) -> None:
    """Execute a notebook with papermill, injecting config_name."""
    input_path = NOTEBOOKS_DIR / f"{notebook_name}.py"
    output_path = output_dir / f"{notebook_name}.ipynb"

    notebook_jupytext = jupytext.read(input_path)

    # Write the .py file as .ipynb
    in_notebook = output_dir / f"{notebook_name}_unexecuted.ipynb"
    in_notebook.parent.mkdir(exist_ok=True, parents=True)
    jupytext.write(notebook_jupytext, in_notebook, fmt="ipynb")

    print(f"\n{'='*60}")
    print(f"Running {notebook_name} with config={config_name}")
    if n_jobs != 1 and notebook_name == "5195_optimise":
        print(f"  (parallel mode: n_jobs={n_jobs})")
    print(f"{'='*60}")

    # Inject config_name and n_jobs parameters
    parameters = {"config_name": config_name}
    if notebook_name == "5195_optimise":
        parameters["n_jobs"] = n_jobs

    pm.execute_notebook(
        str(in_notebook),
        str(output_path),
        parameters=parameters,
        kernel_name="python3",
    )
    print(f"  -> Saved to {output_path}")


def resolve_step(name: str) -> str:
    """Match a partial step name to a full step name."""
    matches = [s for s in ALL_STEPS if name in s]
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        print(f"Error: no step matching '{name}'. Available: {ALL_STEPS}", file=sys.stderr)
        sys.exit(1)
    # Try exact prefix match on the numeric part
    exact = [s for s in matches if s.startswith(name)]
    if len(exact) == 1:
        return exact[0]
    print(f"Error: '{name}' is ambiguous, matches: {matches}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the FLEX pipeline",
        epilog="Steps: " + ", ".join(ALL_STEPS),
    )
    parser.add_argument("config_name", help="Name of the YAML config (without .yaml)")
    parser.add_argument(
        "--from", dest="start_from", metavar="STEP",
        help="Resume from this step (skips earlier steps). "
             "Accepts partial match, e.g. '5201' or '5195'.",
    )
    parser.add_argument(
        "--only", metavar="STEP",
        help="Run only this single step.",
    )
    parser.add_argument(
        "--parallel", "--n-jobs", dest="n_jobs", type=int, metavar="N",
        help="Run optimization in parallel with N jobs. Use -1 for all cores (capped at 20). "
             "Explicitly specify >20 to override the cap. Only affects the optimization step (5195_optimise).",
        default=1,
    )
    args = parser.parse_args()

    config_name = args.config_name

    # Verify config exists
    config_path = REPO_ROOT / "configs" / f"{config_name}.yaml"
    if not config_path.exists():
        print(f"Error: config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    # Load config to check for optimization
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from flex.config import load_config

    cfg = load_config(config_name)
    has_optimization = bool(cfg.optimization)

    # Build full pipeline sequence
    steps = ["5191_extension"]
    if has_optimization:
        steps.extend(["5195_optimise", "5196_apply_optimised"])
    steps.extend(["5201_extension_fair_simulations", "5202_extension_fair_plots"])

    # Apply --only
    if args.only:
        step = resolve_step(args.only)
        steps = [step]

    # Apply --from
    if args.start_from:
        step = resolve_step(args.start_from)
        if step not in steps:
            print(f"Error: step '{step}' not in pipeline for this config.", file=sys.stderr)
            sys.exit(1)
        idx = steps.index(step)
        skipped = steps[:idx]
        steps = steps[idx:]
        if skipped:
            print(f"Skipping: {' -> '.join(skipped)}")

    # Output directory for rendered notebooks
    output_dir = REPO_ROOT / "outputs" / config_name / "notebooks"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pipeline for '{config_name}': {' -> '.join(steps)}")
    if has_optimization:
        print(f"Optimization enabled for: {list(cfg.optimization.keys())}")
        if args.n_jobs != 1:
            import os
            if args.n_jobs == -1:
                n_jobs_display = f"{min(os.cpu_count() or 1, 20)} jobs (capped at 20)"
            elif args.n_jobs > 20:
                n_jobs_display = f"{args.n_jobs} jobs (explicit override)"
            else:
                n_jobs_display = f"{args.n_jobs} jobs"
            print(f"Parallel optimization: {n_jobs_display}")

    for notebook_name in steps:
        run_notebook(notebook_name, config_name, output_dir, n_jobs=args.n_jobs)

    print(f"\nPipeline complete. Rendered notebooks in {output_dir}")


if __name__ == "__main__":
    main()
