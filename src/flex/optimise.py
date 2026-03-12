"""Optimization of extension parameters to meet FaIR temperature targets.

Adjusts fossil CO2 storyline parameters so that FaIR median temperature
holds steady at a specified level (e.g., the departure-year peak).
"""

import numpy as np
import pandas as pd
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties
from scipy.optimize import differential_evolution

from flex.config import DATA_DIR, FlexConfig


def setup_fair(
    emissions_csv: str | pd.DataFrame,
    scenarios: list[str],
    memory_limited: bool = True,
    scenario_mapping: dict[str, str] | None = None,
) -> FAIR:
    """Set up a FaIR instance ready to run.

    Parameters
    ----------
    emissions_csv
        Path to the FaIR-format emissions CSV, or a DataFrame already loaded.
    scenarios
        List of scenario short names (e.g. ["LN"]).
    memory_limited
        If True, use 5-member ensemble; otherwise full ~1000 member.
    scenario_mapping
        Maps new scenario names to base scenarios for the forcing file.
        E.g. {"HL-CF": "HL"} means HL-CF reuses HL's volcanic/solar forcing.

    Returns
    -------
    Configured FAIR instance (not yet run).
    """
    fair_inputs = DATA_DIR / "fair-inputs"

    f = FAIR()
    f.define_time(1750, 2501, 1)
    f.define_scenarios(scenarios)

    species, properties = read_properties(
        str(fair_inputs / "species_configs_properties_1.4.1.csv")
    )
    f.define_species(species, properties)
    f.ch4_method = "Thornhill2021"

    if memory_limited:
        params_file = fair_inputs / "1.5.0" / "calibrated_constrained_parameters_short.csv"
    else:
        params_file = fair_inputs / "1.5.0" / "calibrated_constrained_parameters.csv"

    df_configs = pd.read_csv(params_file, index_col=0)
    f.define_configs(df_configs.index)
    f.allocate()

    # Prepare forcing file: add rows for new scenarios not in the original
    forcing_path = str(fair_inputs / "volcanic_solar.csv")
    if scenario_mapping:
        import tempfile
        df_forcing = pd.read_csv(forcing_path)
        existing = set(df_forcing["Scenario"].unique())
        new_rows = []
        for new_scen, base_scen in scenario_mapping.items():
            if new_scen not in existing and base_scen in existing:
                rows = df_forcing[df_forcing["Scenario"] == base_scen].copy()
                rows["Scenario"] = new_scen
                new_rows.append(rows)
        if new_rows:
            df_forcing = pd.concat([df_forcing] + new_rows, ignore_index=True)
            tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
            df_forcing.to_csv(tmp, index=False)
            tmp.close()
            forcing_path = tmp.name

    # Load emissions and forcing
    if isinstance(emissions_csv, (str, type(DATA_DIR))):
        f.fill_from_csv(
            forcing_file=forcing_path,
            emissions_file=str(emissions_csv),
        )
    else:
        raise TypeError("Pass a path to the emissions CSV")

    # Zero out solar forcing
    for s in f.scenarios:
        f.forcing.loc[dict(scenario=s, specie="Solar")] = 0

    # Fill species configs and calibrated parameters
    f.fill_species_configs(str(fair_inputs / "species_configs_properties_1.4.1.csv"))
    f.override_defaults(str(params_file))

    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)

    return f


def run_fair_single_scenario(
    emissions_csv_path: str,
    scenario: str,
    memory_limited: bool = True,
    base_scenario: str | None = None,
) -> np.ndarray:
    """Run FaIR for a single scenario and return median temperature.

    Parameters
    ----------
    base_scenario
        If the scenario is new (not in the forcing file), map it to this
        base scenario for volcanic/solar forcing.

    Returns
    -------
    1D array of median surface temperature (751 timebounds, 1750-2500).
    """
    mapping = None
    if base_scenario:
        mapping = {scenario: base_scenario}
    f = setup_fair(
        emissions_csv_path, [scenario],
        memory_limited=memory_limited,
        scenario_mapping=mapping,
    )
    f.run()
    temp = f.temperature.sel(scenario=scenario, layer=0)
    return temp.median(dim="config").values


def modify_emissions_csv(
    base_csv_path: str,
    scenario: str,
    new_scenario: str,
    co2_ffi_trajectory: np.ndarray | None = None,
    ch4_trajectory: np.ndarray | None = None,
    departure_year: int = 2080,
    output_path: str | None = None,
) -> str:
    """Create a modified emissions CSV with adjusted trajectories for one scenario.

    Takes the base emissions CSV, duplicates a scenario under a new name,
    and replaces CO2 FFI and/or CH4 trajectories from departure_year onward.

    Parameters
    ----------
    base_csv_path
        Path to the original FaIR emissions CSV.
    scenario
        Source scenario short name (e.g. "LN").
    new_scenario
        New scenario short name (e.g. "LN-CF").
    co2_ffi_trajectory
        Full CO2 FFI trajectory (all 752 timepoints). If None, keeps original.
    ch4_trajectory
        Full CH4 trajectory (all 752 timepoints). If None, keeps original.
    departure_year
        Year at which modified trajectories diverge from base.
    output_path
        Where to write the modified CSV. If None, returns the path.

    Returns
    -------
    Path to the modified CSV.
    """
    df = pd.read_csv(base_csv_path)

    # Get all rows for the source scenario
    source_rows = df[df["scenario"] == scenario].copy()

    # Duplicate under new scenario name
    new_rows = source_rows.copy()
    new_rows["scenario"] = new_scenario

    # Year columns are like "1750.5", "1751.5", ...
    year_cols = [c for c in df.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    departure_idx = np.searchsorted(years, departure_year + 0.5)

    # Replace CO2 FFI from departure_year onward
    if co2_ffi_trajectory is not None:
        mask = new_rows["variable"] == "CO2 FFI"
        for i, col in enumerate(year_cols):
            if i >= departure_idx:
                new_rows.loc[mask, col] = co2_ffi_trajectory[i]

    # Replace CH4 from departure_year onward
    if ch4_trajectory is not None:
        mask = new_rows["variable"] == "CH4"
        for i, col in enumerate(year_cols):
            if i >= departure_idx:
                new_rows.loc[mask, col] = ch4_trajectory[i]

    # Drop any pre-existing rows for new_scenario (e.g. from a naive 5191 extension)
    # so we replace rather than duplicate.
    df = df[df["scenario"] != new_scenario]

    # Combine: original + new scenario
    df_out = pd.concat([df, new_rows], ignore_index=True)

    if output_path is None:
        output_path = base_csv_path.replace(".csv", f"_{new_scenario}.csv")

    df_out.to_csv(output_path, index=False)
    return output_path


def build_co2_trajectory_from_ecs_params(
    base_emissions_csv: str,
    scenario: str,
    exp_targ: float,
    sig_start: float,
    sig_end: float,
    departure_year: int = 2080,
    exp_end: int | None = None,
    roll_in: int = 20,
    roll_out: int = 20,
) -> np.ndarray:
    """Build a CO2 FFI trajectory using ECS storyline logic.

    Uses the existing storyline functions to generate CO2 from departure_year.

    Returns
    -------
    Full trajectory array (752 timepoints matching FaIR emissions CSV).
    """
    from flex.fossil_co2_storyline_functions import (
        extend_co2_for_scen_storyline,
    )

    df = pd.read_csv(base_emissions_csv)
    source = df[(df["scenario"] == scenario) & (df["variable"] == "CO2 FFI")]
    year_cols = [c for c in df.columns if c.replace(".", "").replace("-", "").isdigit()]
    base_values = source[year_cols].values.flatten()

    if exp_end is None:
        exp_end = int(sig_start)

    # The trajectory from departure_year onward is what we control
    # Return the full array, unmodified before departure_year
    return base_values, year_cols


def build_ch4_plateau_trajectory(
    base_emissions_csv: str,
    scenario: str,
    ch4_target: float,
    departure_year: int = 2080,
    transition_years: int = 20,
) -> np.ndarray:
    """Build a CH4 trajectory that transitions to a constant level.

    From departure_year, linearly transitions to ch4_target over
    transition_years, then holds constant.

    Returns
    -------
    Full trajectory array (752 timepoints).
    """
    df = pd.read_csv(base_emissions_csv)
    source = df[(df["scenario"] == scenario) & (df["variable"] == "CH4")]
    year_cols = [c for c in df.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    values = source[year_cols].values.flatten().copy()

    dep_idx = np.searchsorted(years, departure_year + 0.5)
    dep_value = values[dep_idx]

    # Linear transition then constant
    for i in range(dep_idx, len(values)):
        yr = years[i] - departure_year
        if yr <= transition_years:
            values[i] = dep_value + (ch4_target - dep_value) * yr / transition_years
        else:
            values[i] = ch4_target

    return values


def _objective_plateau(
    params: np.ndarray,
    *,
    optimize_params: list[str],
    fixed_params: dict[str, float],
    base_emissions_csv: str,
    base_scenario: str,
    new_scenario: str,
    ch4_trajectory: np.ndarray,
    departure_year: int,
    target_temp: float,
    temp_csv_path: str,
    memory_limited: bool = True,
    forcing_scenario: str | None = None,
) -> float:
    """Objective function: squared temperature deviation from target post-departure.

    Parameters
    ----------
    params
        Values for the parameters listed in optimize_params.
    optimize_params
        Names of parameters being optimized (subset of [exp_targ, sig_start, sig_end]).
    fixed_params
        Parameters held fixed (e.g. {"sig_end": 2300}).
    """
    # Map optimized + fixed params into the three ECS values
    all_params = dict(zip(optimize_params, params)) | fixed_params
    exp_targ = all_params["exp_targ"]
    sig_start = all_params["sig_start"]
    sig_end = all_params["sig_end"]

    # Enforce ordering constraint
    if sig_start >= sig_end:
        return 1e6

    # Build modified CO2 FFI trajectory
    # Read base emissions, modify from departure_year using simple interpolation
    df = pd.read_csv(base_emissions_csv)
    source = df[(df["scenario"] == base_scenario) & (df["variable"] == "CO2 FFI")]
    year_cols = [c for c in df.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    co2_values = source[year_cols].values.flatten().copy()

    dep_idx = np.searchsorted(years, departure_year + 0.5)
    dep_value = co2_values[dep_idx]

    # Phase 1: linear from departure_value to exp_targ by exp_end (= sig_start for simplicity)
    exp_end = int(sig_start)
    for i in range(dep_idx, len(co2_values)):
        yr = years[i] - departure_year
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            frac = yr / yr_total
            co2_values[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            co2_values[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            # Sigmoid to zero
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            # Smooth sigmoid
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3  # smoothstep
            co2_values[i] = exp_targ * (1 - s)
        else:
            co2_values[i] = 0.0

    # Write modified CSV
    modified_csv = modify_emissions_csv(
        base_emissions_csv,
        base_scenario,
        new_scenario,
        co2_ffi_trajectory=co2_values,
        ch4_trajectory=ch4_trajectory,
        departure_year=departure_year,
        output_path=temp_csv_path,
    )

    # Run FaIR
    try:
        temp_median = run_fair_single_scenario(
            modified_csv, new_scenario,
            memory_limited=memory_limited,
            base_scenario=forcing_scenario or base_scenario,
        )
    except Exception as e:
        print(f"FaIR failed with params {params}: {e}")
        return 1e6

    # Compute cost: sum of squared deviations from target_temp after departure
    timebounds = np.arange(1750, 2501, 1.0)
    dep_bound_idx = np.searchsorted(timebounds, departure_year)
    post_dep_temp = temp_median[dep_bound_idx:]

    cost = np.sum((post_dep_temp - target_temp) ** 2)
    opt_str = ", ".join(f"{k}={all_params[k]:.0f}" for k in optimize_params)
    print(f"  {opt_str} -> cost={cost:.4f}")
    return cost


def optimize_scenario(
    cfg: FlexConfig,
    marker: str,
    base_emissions_csv: str,
    memory_limited: bool = True,
) -> dict:
    """Optimize fossil evolution parameters for a scenario to achieve temperature plateau.

    Parameters
    ----------
    cfg
        FLEX configuration with optimization settings.
    marker
        Marker key to optimize (e.g. "LN-CF").
    base_emissions_csv
        Path to FaIR emissions CSV with all standard scenarios.
    memory_limited
        Use reduced ensemble for speed.

    Returns
    -------
    Dict with optimized params, target temperature, and final cost.
    """
    opt_settings = cfg.optimization[marker]
    departure_year = opt_settings["departure_year"]
    bounds_cfg = opt_settings["bounds"]

    base_scenario = cfg.scenario_model_match[marker][0]
    # Find the source marker that shares the same scenario/model
    # (LN-CF uses LN's base data)
    source_marker = None
    for m, info in cfg.scenario_model_match.items():
        if m != marker and info[0] == base_scenario and info[1] == cfg.scenario_model_match[marker][1]:
            source_marker = m
            break

    if source_marker is None:
        msg = f"No source marker found for {marker} (scenario={base_scenario})"
        raise ValueError(msg)

    forcing_scen = cfg.forcing_scenario.get(source_marker, source_marker)
    print(f"Optimizing {marker} based on {source_marker} (departure {departure_year}, forcing={forcing_scen})")

    # Step 1: Get target temperature from source scenario at departure year
    print("Running baseline FaIR to get target temperature...")
    temp_baseline = run_fair_single_scenario(
        base_emissions_csv, source_marker, memory_limited=memory_limited,
        base_scenario=forcing_scen if forcing_scen != source_marker else None,
    )
    timebounds = np.arange(1750, 2501, 1.0)
    dep_idx = np.searchsorted(timebounds, departure_year)
    target_temp = temp_baseline[dep_idx]
    print(f"Target temperature at {departure_year}: {target_temp:.4f} K")

    # Step 2: Build CH4 plateau trajectory (fixed, not optimized)
    ch4_target = cfg.component_global_targets.get("Emissions|CH4", {}).get(marker, 200.0)
    ch4_traj = build_ch4_plateau_trajectory(
        base_emissions_csv,
        source_marker,
        ch4_target=ch4_target,
        departure_year=departure_year,
    )
    print(f"CH4 target: {ch4_target} Mt/yr")

    # Step 3: Optimize CO2 params
    temp_csv = str(cfg.outputs_dir / "_temp_optimization_emissions.csv")
    optimize_params = opt_settings.get("optimize_params", ["exp_targ", "sig_start", "sig_end"])
    fixed_params = opt_settings.get("fixed_params", {})
    bounds = [tuple(bounds_cfg[p]) for p in optimize_params]

    print(f"Optimizing: {optimize_params}")
    if fixed_params:
        print(f"Fixed: {fixed_params}")

    result = differential_evolution(
        lambda params: _objective_plateau(
            params,
            optimize_params=optimize_params,
            fixed_params=fixed_params,
            base_emissions_csv=base_emissions_csv,
            base_scenario=source_marker,
            new_scenario=marker,
            ch4_trajectory=ch4_traj,
            departure_year=departure_year,
            target_temp=target_temp,
            temp_csv_path=temp_csv,
            memory_limited=memory_limited,
            forcing_scenario=forcing_scen,
        ),
        bounds=bounds,
        seed=42,
        maxiter=15,
        tol=0.01,
        atol=0.5,
        popsize=5,
        polish=True,
        disp=True,
    )

    # Map result back to named params
    all_params = dict(zip(optimize_params, result.x)) | fixed_params
    optimized = {
        "exp_targ": all_params["exp_targ"],
        "sig_start": all_params["sig_start"],
        "sig_end": all_params["sig_end"],
        "target_temp": target_temp,
        "final_cost": result.fun,
        "success": result.success,
        "message": result.message,
        "departure_year": departure_year,
        "ch4_target": ch4_target,
        "ch4_trajectory": ch4_traj,
    }

    print(f"\nOptimization {'succeeded' if result.success else 'did not converge'}:")
    print(f"  exp_targ  = {all_params['exp_targ']:.1f}")
    print(f"  sig_start = {all_params['sig_start']:.1f}")
    print(f"  sig_end   = {all_params['sig_end']:.1f}")
    print(f"  cost      = {result.fun:.6f}")

    return optimized
