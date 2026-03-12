"""Configuration loader for FLEX extension pipeline.

Loads YAML config files and converts them to the dict formats
expected by the existing extension functions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Default paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"


@dataclass
class FlexConfig:
    """Configuration for a single FLEX extension ensemble run."""

    name: str
    description: str

    # Time constants
    historical_start_year: int
    future_start_year: float
    scenario_end_year: int
    extensions_end_year: int

    # Flags
    make_plots: bool
    dump_csvs: bool

    # The four core configuration dicts (in notebook-compatible format)
    scenario_model_match: dict[str, list]
    fossil_evolution_dictionary: dict[str, list]
    removal_dictionary: dict[str, list]
    component_global_targets: dict[str, dict]

    # Plot colors per marker
    plot_colors: dict[str, str]

    # Derived paths
    outputs_dir: Path = field(init=False)
    plots_dir: Path = field(init=False)

    def __post_init__(self):
        self.outputs_dir = REPO_ROOT / "outputs" / self.name
        self.plots_dir = REPO_ROOT / "plots" / self.name
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)


def _convert_scenario_model_match(raw: dict[str, dict]) -> dict[str, list]:
    """Convert YAML scenario_model_match to notebook-expected format.

    YAML: {VL: {scenario: ..., model: ..., color: ...}}
    Notebook: {VL: [scenario, model, color]}
    """
    return {
        marker: [entry["scenario"], entry["model"], entry["color"]]
        for marker, entry in raw.items()
    }


def _convert_fossil_evolution(raw: dict[str, dict]) -> dict[str, list]:
    """Convert YAML fossil_evolution to notebook-expected format.

    YAML: {VL: {type: ECS, params: [...]}}
    Notebook: {VL: ["ECS", ...params]}
    """
    return {
        marker: [entry["type"]] + entry["params"]
        for marker, entry in raw.items()
    }


def _convert_removal_strategy(raw: dict[str, dict]) -> dict[str, list]:
    """Convert YAML removal_strategy to notebook-expected format.

    YAML: {VL: {type: NEG, params: [100, 60]}}
    Notebook: {VL: ["NEG", 100, 60]}
    """
    return {
        marker: [entry["type"]] + entry.get("params", [])
        for marker, entry in raw.items()
    }


def load_config(name: str, configs_dir: Path | None = None) -> FlexConfig:
    """Load a FLEX configuration by name.

    Parameters
    ----------
    name
        Config name (without .yaml extension), e.g. "scenariomip_default"
    configs_dir
        Directory containing YAML configs. Defaults to {repo}/configs/

    Returns
    -------
    FlexConfig with all parameters populated and output dirs created.
    """
    if configs_dir is None:
        configs_dir = CONFIGS_DIR

    config_path = configs_dir / f"{name}.yaml"
    if not config_path.exists():
        available = [p.stem for p in configs_dir.glob("*.yaml")]
        msg = f"Config '{name}' not found at {config_path}. Available: {available}"
        raise FileNotFoundError(msg)

    with open(config_path) as fh:
        raw = yaml.safe_load(fh)

    return FlexConfig(
        name=raw["name"],
        description=raw.get("description", ""),
        # Time
        historical_start_year=raw["time"]["historical_start_year"],
        future_start_year=raw["time"]["future_start_year"],
        scenario_end_year=raw["time"]["scenario_end_year"],
        extensions_end_year=raw["time"]["extensions_end_year"],
        # Flags
        make_plots=raw["flags"]["make_plots"],
        dump_csvs=raw["flags"]["dump_csvs"],
        # Core dicts (converted to notebook-compatible format)
        scenario_model_match=_convert_scenario_model_match(raw["scenario_model_match"]),
        fossil_evolution_dictionary=_convert_fossil_evolution(raw["fossil_evolution"]),
        removal_dictionary=_convert_removal_strategy(raw["removal_strategy"]),
        component_global_targets=raw["non_co2_targets"],
        plot_colors=raw.get("plot_colors", {}),
    )


def list_configs(configs_dir: Path | None = None) -> list[str]:
    """List available configuration names."""
    if configs_dir is None:
        configs_dir = CONFIGS_DIR
    return sorted(p.stem for p in configs_dir.glob("*.yaml"))
