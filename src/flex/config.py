"""Configuration loader for FLEX extension pipeline.

Loads YAML config files and converts them to the dict formats
expected by the existing extension functions.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Default paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"

# Where the input data lives. Defaults to <repo>/data, but set FLEX_DATA_DIR to
# keep your working copies outside the repository. The scenario files are no
# longer tracked here, so a checkout of a pre-2026 commit will overwrite them and
# checking back out will delete them again; holding them outside the working tree
# avoids that entirely. See data/README.md.
DATA_DIR = Path(os.environ.get("FLEX_DATA_DIR") or REPO_ROOT / "data").expanduser()

# --- FaIR calibration inputs -------------------------------------------------
# Single source of truth for the FaIR calibrated-constrained parameter set, so
# the package, the notebooks and scripts/fetch_data.py can never drift onto
# different calibration vintages.  To move to a new calibration, bump the
# version, the record DOI and the hash together.
#
# 1.6.0 is the CMIP7-era calibration (841 members), Zenodo record 18828694.
# The concept DOI 10.5281/zenodo.7112539 always resolves to the *latest*
# record, so the version-specific record DOI is used here to keep fetches
# reproducible.
FAIR_CALIBRATION_VERSION = "1.6.0"
FAIR_CALIBRATION_DOI = "10.5281/zenodo.18828694"
FAIR_PARAMS_FILE_NAME = "calibrated_constrained_parameters.csv"
FAIR_PARAMS_FILE_HASH = "md5:b0fadc337e7b66525703f5b7f5fce2db"

FAIR_INPUTS_DIR = DATA_DIR / "fair-inputs"
FAIR_PARAMS_FILE = FAIR_INPUTS_DIR / FAIR_CALIBRATION_VERSION / FAIR_PARAMS_FILE_NAME
FAIR_SPECIES_FILE = FAIR_INPUTS_DIR / "species_configs_properties_1.4.1.csv"
FAIR_FORCING_FILE = FAIR_INPUTS_DIR / "volcanic_solar.csv"

# Ensemble size used when a caller asks for a small, fast run and does not name
# an explicit n_configs.  Members are drawn evenly spaced from FAIR_PARAMS_FILE
# so the reduced ensemble is always a subset of the calibration in use.
FAIR_SMALL_ENSEMBLE_SIZE = 5

# The single calibration member WIEMIP uses as its default FaIR configuration.
# Its individual trajectory is reported alongside the ensemble median, so it is
# force-included in the ensemble even when subsampling would drop it (it sits at
# position 448 of 841 and is not picked by the evenly-spaced subsample).
# Present in calibration 1.6.0 only; set to None to report the median alone.
FAIR_REFERENCE_CONFIG = 867236
FAIR_REFERENCE_CONFIG_LABEL = "WIEMIP default (config 867236)"


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




    # The four core configuration dicts (in notebook-compatible format)
    scenario_model_match: dict[str, list]
    fossil_evolution_dictionary: dict[str, list]
    removal_dictionary: dict[str, list]
    component_global_targets: dict[str, dict]

    # Flags
    make_plots: bool = False
    dump_csvs: bool  = False
    read_non_co2_from_csv: bool = False
    read_afolu_from_csv: bool = False
    # When True, 5196 regionalises/sectorises the optimised counterfactual
    # fossil CO2 and writes a full extended_scenarios CSV alongside the
    # global FaIR-format output.
    regionalize_optimised_output: bool = False

    # Optimization settings (empty dict if no optimization configured)
    optimization: dict[str, dict] = field(default_factory=dict)
    # Optional alternate data sources (paths relative to DATA_DIR)
    data_sources: dict | None = None
    # Maps marker names to volcanic_solar.csv scenario IDs (e.g. "VL")
    forcing_scenario: dict[str, str] = field(default_factory=dict)
    # Optional concentrations file: when set, all non-CO2 GHG species are
    # run in concentration-driven mode using this file (path relative to DATA_DIR).
    concentrations_file: str | None = None
    # Derived paths
    outputs_dir: Path = field(init=False)
    plots_dir: Path = field(init=False)

    def __post_init__(self):
        self.outputs_dir = REPO_ROOT / "outputs" / self.name
        self.plots_dir = REPO_ROOT / "plots" / self.name
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    @property
    def scenario_mapping(self) -> dict[str, str]:
        """Map counterfactual markers to their source markers for FaIR forcing.

        Returns a dict like ``{"HL-CF": "HL"}`` for scenarios that share the
        same underlying SSP scenario + model with another marker.  If no
        counterfactual scenarios exist the dict is empty.
        """
        # Build reverse lookup: (scenario, model) -> first marker that uses it
        seen: dict[tuple[str, str], str] = {}
        mapping: dict[str, str] = {}
        for marker, info in self.scenario_model_match.items():
            key = (info[0], info[1])
            if key in seen:
                mapping[marker] = seen[key]
            else:
                seen[key] = marker
        return mapping

    @property
    def markers(self) -> list[str]:
        """Ordered list of all marker names from the config."""
        return list(self.scenario_model_match.keys())


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


def _normalize_non_co2_targets(raw_targets: dict[str, dict]) -> dict[str, dict]:
    """Normalize non_co2_targets entries to a consistent dict format.

    Accepts three formats per scenario entry:
    - bare number (e.g. 95.0) → {"target": 95.0}
    - null/None → {"target": None} (auto-calculate target from data)
    - dict with at least "target" key → passed through

    Scenarios not listed under a variable are not extended for that
    variable (they keep the source scenario data).
    """
    normalized: dict[str, dict] = {}
    for variable, scenarios in raw_targets.items():
        normalized[variable] = {}
        for marker, value in scenarios.items():
            if value is None:
                normalized[variable][marker] = {"target": None}
            elif isinstance(value, dict):
                normalized[variable][marker] = value
            else:
                normalized[variable][marker] = {"target": float(value)}
    return normalized


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
        make_plots=raw["flags"].get("make_plots", False),
        dump_csvs=raw["flags"].get("dump_csvs", False),
        read_non_co2_from_csv=raw["flags"].get("read_non_co2_from_csv", False),
        read_afolu_from_csv=raw["flags"].get("read_afolu_from_csv", False),
        regionalize_optimised_output=raw["flags"].get("regionalize_optimised_output", False),
        # Core dicts (converted to notebook-compatible format)
        scenario_model_match=_convert_scenario_model_match(raw["scenario_model_match"]),
        fossil_evolution_dictionary=_convert_fossil_evolution(raw["fossil_evolution"]),
        removal_dictionary=_convert_removal_strategy(raw["removal_strategy"]),
        component_global_targets=_normalize_non_co2_targets(raw["non_co2_targets"]),
        optimization=raw.get("optimization", {}),
        data_sources=raw.get("data_sources", None),
        forcing_scenario=raw.get("forcing_scenario", {}),
        concentrations_file=raw.get("concentrations_file", None),
    )


def list_configs(configs_dir: Path | None = None) -> list[str]:
    """List available configuration names."""
    if configs_dir is None:
        configs_dir = CONFIGS_DIR
    return sorted(p.stem for p in configs_dir.glob("*.yaml"))
