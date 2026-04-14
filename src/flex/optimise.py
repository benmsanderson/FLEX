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
    n_configs: int | None = None,
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
        Ignored when *n_configs* is set.
    scenario_mapping
        Maps new scenario names to base scenarios for the forcing file.
        E.g. {"HL-CF": "HL"} means HL-CF reuses HL's volcanic/solar forcing.
    n_configs
        Explicit number of configs to use, drawn evenly-spaced from the
        full ~1000-member parameter set.  Overrides *memory_limited* when
        set.  Use 1 for a fast deterministic run during optimization.

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

    if n_configs is not None:
        # Always draw from the full parameter set so any ensemble size
        # from 1 up to ~1000 is representative.
        params_file = fair_inputs / "1.5.0" / "calibrated_constrained_parameters.csv"
    elif memory_limited:
        params_file = fair_inputs / "1.5.0" / "calibrated_constrained_parameters_short.csv"
    else:
        params_file = fair_inputs / "1.5.0" / "calibrated_constrained_parameters.csv"

    df_configs = pd.read_csv(params_file, index_col=0)
    if n_configs is not None and n_configs < len(df_configs):
        indices = np.linspace(0, len(df_configs) - 1, n_configs, dtype=int)
        df_configs = df_configs.iloc[indices]
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
    f.climate_configs["stochastic_run"][:] = False

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
    n_configs: int | None = None,
) -> np.ndarray:
    """Run FaIR for a single scenario and return median temperature.

    Parameters
    ----------
    base_scenario
        If the scenario is new (not in the forcing file), map it to this
        base scenario for volcanic/solar forcing.
    n_configs
        Explicit number of configs (passed to *setup_fair*).

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
        n_configs=n_configs,
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


def _build_co2_trajectory(
    base_co2_ffi: np.ndarray,
    base_co2_afolu: np.ndarray,
    years: np.ndarray,
    departure_year: int,
    exp_targ: float,
    sig_start: float,
    sig_end: float,
) -> np.ndarray:
    """Build CO2 FFI trajectory from a total-CO2 target profile.

    Defines total CO2 (FFI + AFOLU) as: linear ramp -> hold -> smoothstep -> zero,
    then derives FFI = total - AFOLU.
    """
    total = (base_co2_ffi + base_co2_afolu).copy()
    dep_idx = np.searchsorted(years, departure_year + 0.5)
    dep_value = total[dep_idx]
    exp_end = int(sig_start)

    for i in range(dep_idx, len(total)):
        yr = years[i] - departure_year
        yr_total = exp_end - departure_year
        if years[i] <= exp_end + 0.5 and yr_total > 0:
            frac = yr / yr_total
            total[i] = dep_value + (exp_targ - dep_value) * min(frac, 1.0)
        elif years[i] <= sig_start + 0.5:
            total[i] = exp_targ
        elif years[i] <= sig_end + 0.5:
            frac = (years[i] - sig_start) / (sig_end - sig_start)
            t = np.clip(frac, 0, 1)
            s = 3 * t**2 - 2 * t**3
            total[i] = exp_targ * (1 - s)
        else:
            total[i] = 0.0

    # Derive FFI = total - AFOLU
    ffi = base_co2_ffi.copy()
    ffi[dep_idx:] = total[dep_idx:] - base_co2_afolu[dep_idx:]
    return ffi


def _objective_plateau(
    params: np.ndarray,
    *,
    optimize_params: list[str],
    fixed_params: dict[str, float],
    base_emissions_csv: str,
    base_scenario: str,
    new_scenario: str,
    departure_year: int,
    target_temp: float,
    temp_csv_path: str,
    memory_limited: bool = True,
    forcing_scenario: str | None = None,
    n_configs: int | None = None,
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

    # Build modified CO2 FFI trajectory via total CO2 target
    df = pd.read_csv(base_emissions_csv)
    source_ffi = df[(df["scenario"] == base_scenario) & (df["variable"] == "CO2 FFI")]
    source_afolu = df[(df["scenario"] == base_scenario) & (df["variable"] == "CO2 AFOLU")]
    year_cols = [c for c in df.columns if c.replace(".", "").replace("-", "").isdigit()]
    years = np.array([float(c) for c in year_cols])
    co2_ffi = source_ffi[year_cols].values.flatten().copy()
    co2_afolu = source_afolu[year_cols].values.flatten().copy() if len(source_afolu) else np.zeros_like(co2_ffi)

    co2_values = _build_co2_trajectory(
        co2_ffi, co2_afolu, years, departure_year,
        exp_targ, sig_start, sig_end,
    )

    # Write modified CSV (only CO2 FFI modified, all other species from source)
    modified_csv = modify_emissions_csv(
        base_emissions_csv,
        base_scenario,
        new_scenario,
        co2_ffi_trajectory=co2_values,
        departure_year=departure_year,
        output_path=temp_csv_path,
    )

    # Run FaIR
    try:
        temp_median = run_fair_single_scenario(
            modified_csv, new_scenario,
            memory_limited=memory_limited,
            base_scenario=forcing_scenario or base_scenario,
            n_configs=n_configs,
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


def _batch_objective_plateau(
    x: np.ndarray,
    *,
    optimize_params: list[str],
    fixed_params: dict[str, float],
    base_scenario: str,
    departure_year: int,
    target_temp: float,
    temp_csv_path: str,
    memory_limited: bool,
    forcing_scenario: str | None,
    n_configs: int | None,
    base_df: pd.DataFrame,
    base_co2_ffi: np.ndarray,
    base_co2_afolu: np.ndarray,
    years: np.ndarray,
    year_cols: list[str],
) -> np.ndarray | float:
    """Vectorized objective: evaluate N candidates in one FaIR run.

    Accepts ``(D, N)`` from ``differential_evolution(vectorized=True)``
    or ``(D,)`` during the polish step.
    """
    if x.ndim == 1:
        x = x.reshape(-1, 1)
        return float(
            _batch_objective_plateau(
                x,
                optimize_params=optimize_params,
                fixed_params=fixed_params,
                base_scenario=base_scenario,
                departure_year=departure_year,
                target_temp=target_temp,
                temp_csv_path=temp_csv_path,
                memory_limited=memory_limited,
                forcing_scenario=forcing_scenario,
                n_configs=n_configs,
                base_df=base_df,
                base_co2_ffi=base_co2_ffi,
                base_co2_afolu=base_co2_afolu,
                years=years,
                year_cols=year_cols,
            )[0]
        )

    n_candidates = x.shape[1]
    costs = np.full(n_candidates, 1e6)

    # Build CO2 trajectories for each valid candidate
    valid: list[tuple[int, str, np.ndarray]] = []
    for j in range(n_candidates):
        params = x[:, j]
        all_p = dict(zip(optimize_params, params)) | fixed_params
        if all_p["sig_start"] >= all_p["sig_end"]:
            continue
        co2 = _build_co2_trajectory(
            base_co2_ffi, base_co2_afolu, years, departure_year,
            all_p["exp_targ"], all_p["sig_start"], all_p["sig_end"],
        )
        valid.append((j, f"_opt_{j}", co2))

    if not valid:
        return costs

    # Assemble one emissions DataFrame with all candidate scenarios
    # Only CO2 FFI is modified; all other species (CH4, N2O, etc.) come
    # from the source scenario as set up by the 5191 extensions.
    source_rows = base_df[base_df["scenario"] == base_scenario]
    dep_idx = int(np.searchsorted(years, departure_year + 0.5))
    post_dep_cols = year_cols[dep_idx:]
    co2_row_mask = source_rows["variable"] == "CO2 FFI"

    new_blocks: list[pd.DataFrame] = []
    scenario_names: list[str] = []
    for _j, scen_name, co2_traj in valid:
        rows = source_rows.copy()
        rows["scenario"] = scen_name
        rows.loc[co2_row_mask, post_dep_cols] = co2_traj[dep_idx:]
        new_blocks.append(rows)
        scenario_names.append(scen_name)

    df_combined = pd.concat(new_blocks, ignore_index=True)
    df_combined.to_csv(temp_csv_path, index=False)

    # Single FaIR run with all candidate scenarios
    base_forcing = forcing_scenario or base_scenario
    mapping = {s: base_forcing for s in scenario_names}
    try:
        f = setup_fair(
            temp_csv_path,
            scenario_names,
            memory_limited=memory_limited,
            scenario_mapping=mapping,
            n_configs=n_configs,
        )
        f.run()
    except Exception as e:
        print(f"Batch FaIR failed: {e}")
        return costs

    # Compute per-candidate cost
    timebounds = np.arange(1750, 2501, 1.0)
    dep_bound_idx = int(np.searchsorted(timebounds, departure_year))
    for j, scen_name, _ in valid:
        temp = f.temperature.sel(scenario=scen_name, layer=0).median(dim="config").values
        post_dep = temp[dep_bound_idx:]
        costs[j] = np.sum((post_dep - target_temp) ** 2)

        params = x[:, j]
        all_p = dict(zip(optimize_params, params)) | fixed_params
        opt_str = ", ".join(f"{k}={all_p[k]:.0f}" for k in optimize_params)
        print(f"  {opt_str} -> cost={costs[j]:.4f}")

    return costs


def optimize_scenario(
    cfg: FlexConfig,
    marker: str,
    base_emissions_csv: str,
    memory_limited: bool = True,
    n_configs: int | None = None,
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
        Use reduced ensemble for speed. Ignored during optimization
        (which always draws from the full parameter set via *n_configs*).
    n_configs
        Number of FaIR climate configs to use during optimization.
        Drawn evenly-spaced from the full ~1000-member calibrated set.
        If *None*, read from the YAML config's ``optimization.<marker>.n_configs``
        (default 1).

    Returns
    -------
    Dict with optimized params, target temperature, and final cost.
    """
    opt_settings = cfg.optimization[marker]
    if n_configs is None:
        n_configs = opt_settings.get("n_configs", 1)
    departure_year_cfg = opt_settings.get("departure_year", "peak")
    target_year_cfg = opt_settings.get("target_year", "peak")
    departure_offset = opt_settings.get("departure_offset", 0)
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
    print(f"Optimizing {marker} based on {source_marker} (forcing={forcing_scen})")

    # Step 1: Run baseline FaIR to determine target temperature
    print(f"Running baseline FaIR ({n_configs} config(s)) to get target temperature...")
    temp_baseline = run_fair_single_scenario(
        base_emissions_csv, source_marker, memory_limited=memory_limited,
        base_scenario=forcing_scen if forcing_scen != source_marker else None,
        n_configs=n_configs,
    )
    timebounds = np.arange(1750, 2501, 1.0)

    # Determine target year / peak year
    peak_idx = int(np.argmax(temp_baseline))
    peak_year = int(timebounds[peak_idx])
    if target_year_cfg == "peak":
        target_year = peak_year
    else:
        target_year = int(target_year_cfg)
    target_temp = temp_baseline[np.searchsorted(timebounds, target_year)]
    print(f"Peak temperature year: {peak_year}")
    print(f"Target year: {target_year}, target temperature: {target_temp:.4f} K")

    # Determine departure year (when trajectory diverges from source)
    if departure_year_cfg == "peak":
        departure_year = peak_year + departure_offset
    else:
        departure_year = int(departure_year_cfg) + departure_offset
    print(f"Departure year: {departure_year}")

    # Step 2: Optimize CO2 params
    # Non-CO2 species (CH4, sulfur, etc.) are already set by the 5191
    # extension step and are taken as-is from the base emissions CSV.
    temp_csv = str(cfg.outputs_dir / "_temp_optimization_emissions.csv")
    optimize_params = opt_settings.get("optimize_params", ["exp_targ", "sig_start", "sig_end"])
    fixed_params = opt_settings.get("fixed_params", {})
    bounds = [tuple(bounds_cfg[p]) for p in optimize_params]

    print(f"Optimizing: {optimize_params}")
    if fixed_params:
        print(f"Fixed: {fixed_params}")

    # Pre-load base emissions once for the vectorized objective
    base_df = pd.read_csv(base_emissions_csv)
    source_co2_ffi = base_df[
        (base_df["scenario"] == source_marker) & (base_df["variable"] == "CO2 FFI")
    ]
    source_co2_afolu = base_df[
        (base_df["scenario"] == source_marker) & (base_df["variable"] == "CO2 AFOLU")
    ]
    year_cols = [c for c in base_df.columns if c.replace(".", "").replace("-", "").isdigit()]
    years_arr = np.array([float(c) for c in year_cols])
    base_co2_ffi_vals = source_co2_ffi[year_cols].values.flatten().copy()
    base_co2_afolu_vals = (
        source_co2_afolu[year_cols].values.flatten().copy()
        if len(source_co2_afolu) else np.zeros_like(base_co2_ffi_vals)
    )

    # Clamp exp_targ upper bound to departure-year total CO2
    # so the trajectory can never jump *up* at the departure point.
    dep_idx_emis = np.searchsorted(years_arr, departure_year + 0.5)
    dep_total_co2 = (base_co2_ffi_vals + base_co2_afolu_vals)[dep_idx_emis]
    if "exp_targ" in optimize_params:
        et_pos = optimize_params.index("exp_targ")
        lo, hi = bounds[et_pos]
        clamped_hi = min(hi, dep_total_co2)
        if lo > clamped_hi:
            # Departure-year CO2 is below configured lower bound (e.g. net-negative);
            # shift the whole search window down, preserving its width.
            width = hi - lo
            clamped_lo = clamped_hi - width
        else:
            clamped_lo = lo
        bounds[et_pos] = (clamped_lo, clamped_hi)
        print(f"Clamped exp_targ bounds to ({clamped_lo:.0f}, {clamped_hi:.0f}) "
              f"[departure-year total CO2: {dep_total_co2:.0f}]")

    result = differential_evolution(
        lambda x: _batch_objective_plateau(
            x,
            optimize_params=optimize_params,
            fixed_params=fixed_params,
            base_scenario=source_marker,
            departure_year=departure_year,
            target_temp=target_temp,
            temp_csv_path=temp_csv,
            memory_limited=memory_limited,
            forcing_scenario=forcing_scen,
            n_configs=n_configs,
            base_df=base_df,
            base_co2_ffi=base_co2_ffi_vals,
            base_co2_afolu=base_co2_afolu_vals,
            years=years_arr,
            year_cols=year_cols,
        ),
        bounds=bounds,
        seed=42,
        maxiter=15,
        tol=0.01,
        atol=0.5,
        popsize=5,
        polish=True,
        disp=True,
        vectorized=True,
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
    }

    print(f"\nOptimization {'succeeded' if result.success else 'did not converge'}:")
    print(f"  exp_targ  = {all_params['exp_targ']:.1f}")
    print(f"  sig_start = {all_params['sig_start']:.1f}")
    print(f"  sig_end   = {all_params['sig_end']:.1f}")
    print(f"  cost      = {result.fun:.6f}")

    return optimized
