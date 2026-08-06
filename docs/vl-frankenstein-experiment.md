# The `vl-frankenstein` experiment

How the VL "Frankenstein" extension ensemble is built, why each configuration choice
was made, and what the pipeline actually does when you run it.

```bash
pixi run pipeline vl-frankenstein
```

Config: [configs/vl-frankenstein.yaml](../configs/vl-frankenstein.yaml)
Companion: [The `WIEMIP` experiment](wiemip-experiment.md)

---

## 1. What the experiment is

The ScenarioMIP VL (SSP1 — Very Low Emissions) marker is a peak-and-decline
pathway. FLEX's job is to carry it from the IAM horizon (2100) out to 2500. The
`vl-frankenstein` config does two things beyond the standard extension:

1. **"Frankenstein" construction.** The pre-2100 scenario is not the vanilla
   REMIND-MAgPIE VL marker. It is a stitched-together variant supplied as a
   bespoke input CSV — hence *Frankenstein* — harmonised from 2015 with
   substituted fossil-fuel (and, in earlier iterations, AFOLU) trajectories. FLEX
   consumes it as if it were a marker and extends it with the usual storyline
   machinery.

2. **A temperature-hold counterfactual.** A second marker, `-hold`, branches off
   the first shortly before its temperature peak and has its post-branch CO2
   trajectory *solved for* rather than prescribed: the fossil CO2 parameters are
   optimised so that FaIR's median temperature stays flat at the peak value all
   the way to 2500. This isolates "what emissions pathway would be needed to
   simply stop warming here?" from the storyline-driven decline of the base case.

The two markers therefore differ **only** in fossil CO2 after the branch year.
Non-CO2, AFOLU, and all forcing inputs are shared, by design.

### Markers

| Marker | Source scenario | Model | Colour | How its CO2 is set |
|---|---|---|---|---|
| `VL-fossil-frankenstein` | `SSP1 - Very Low Emissions Ref1p5` | `REMIND-MAgPIE 3.5-4.11` | `#2196F3` | Prescribed ECS storyline (5191) |
| `VL-fossil-frankenstein-hold` | same | same | `#9C27B0` | Optimised against a FaIR temperature target (5195/5196) |

Two further markers — `VL-fossil-frankenstein-zero-afolu` and its `-hold`
partner, which tested a zero-AFOLU variant — are **commented out** in the current
config. Their parameter blocks are left in place (in `fossil_evolution`,
`removal_strategy`, `non_co2_targets`, `forcing_scenario`) so they can be
re-enabled by uncommenting the two `scenario_model_match` entries. Entries in
those blocks for markers that are not in `scenario_model_match` are simply
ignored by the loader.

---

## 2. Running it

```bash
pixi install                      # once
pixi run pipeline vl-frankenstein
```

`scripts/run_pipeline.py` reads the config, notices it has an `optimization`
section, and therefore executes five papermill steps in order:

```
5191_extension  →  5195_optimise  →  5196_apply_optimised
                →  5201_extension_fair_simulations  →  5202_extension_fair_plots
```

Useful variants:

```bash
pixi run pipeline vl-frankenstein -- --from 5201      # skip straight to the FaIR run
pixi run pipeline vl-frankenstein -- --only 5202      # re-draw the plots
pixi run pipeline vl-frankenstein -- --parallel -1    # parallelise the optimiser
```

`--parallel` only affects step 5195, and only helps when there is more than one
enabled optimisation target. With just `VL-fossil-frankenstein-hold` enabled the
run falls back to sequential mode regardless — 5195 checks
`len(markers_to_optimize) > 1` before spawning joblib workers. It becomes useful
again if the zero-AFOLU markers are re-enabled.

Rendered notebooks land in `outputs/vl-frankenstein/notebooks/`; data outputs in
`outputs/vl-frankenstein/`; figures in `plots/vl-frankenstein/`.

---

## 3. Input data

```yaml
data_sources:
  scenarios_global:
    - "vl-extensions-inputs/VL_Ref1p5_260616.csv"
    - "vl-extensions-inputs/VL_Ref1p5_260616.csv"
  scenarios_regional: "vl-extensions-inputs/VL_Ref1p5_260616.csv"
  regional_scenario_fallback:
    "SSP1 - Very Low Emissions Ref1p5 hold": "SSP1 - Very Low Emissions Ref1p5"
```

The Frankenstein scenario does not live in the repository's standard
`scenarios_complete_global.csv` / `scenarios_regional.csv`. `data_sources`
overrides those loads with a purpose-built delivery. `history` and
`history_regional` are **not** overridden and still come from
`data/history.csv` and `data/history_regional.csv`.

`scenarios_global` is a list because earlier iterations delivered the base and
AFOLU-zero variants as two separate files, which 5191 concatenates. The current
config lists the same path twice — a leftover from that shape. 5191 takes the
`len(_global_dfs) > 1` branch and concatenates the file with itself, so every
global row appears twice. Downstream `pix.ismatch` selections mostly take the
first match or are deduplicated by
`merge_historical_future_timeseries` (which drops duplicate index rows), so this
is survivable rather than correct; collapsing the list to a single entry is the
clean fix.

`regional_scenario_fallback` handles the fact that the `-hold` counterfactual has
no regional breakdown of its own. It clones the base scenario's regional (and, if
absent, global) rows under the fallback name so the regionalisation step has
something to disaggregate against.

### Ensemble bookkeeping: markers share a scenario name

Both markers point at the *same* `(scenario, model)` pair. That is load-bearing:

- `FlexConfig.scenario_mapping` walks `scenario_model_match` in order, records the
  first marker per `(scenario, model)` key, and maps later collisions onto it —
  yielding `{"VL-fossil-frankenstein-hold": "VL-fossil-frankenstein"}`. This is
  how 5195/5196 discover the *source marker* to branch from.
- 5191 processes `scenario_model_match` **minus** anything in `cfg.optimization`,
  so it builds only `VL-fossil-frankenstein`. The `-hold` marker is created later,
  by 5196, from the optimiser's answer.
- `convert_continuous_to_fair_csv` maps long scenario names back to markers with
  `setdefault`, so the shared long name resolves to the non-optimised marker —
  again by design.

### Concentration-driven non-CO2

```yaml
concentrations_file: fair-inputs/concentrations_1750-2500.csv
```

When set, `setup_fair` flips every species with
`input_mode == "emissions" and greenhouse_gas == 1` — excluding `CO2 FFI` and
`CO2 AFOLU` — into concentration-driven mode and fills those series from the CSV
(`_get_conc_driven_species` / `_fill_concentrations_from_file` in
[src/flex/optimise.py](../src/flex/optimise.py)). CH4, N2O, and the halocarbons stop
responding to their emissions; aerosols and ozone precursors stay
emissions-driven.

Two consequences worth stating plainly:

- The optimiser's control variable is genuinely CO2-only. Any CO2-driven
  perturbation of CH4 lifetime or N2O burden is switched off, so the
  temperature-hold solution is a pure carbon-budget answer.
- The `non_co2_targets` for CH4 become inert for forcing purposes: the extended
  CH4 *emissions* are still written to the output CSVs, but FaIR uses the
  prescribed concentrations instead. The Sulfur target still bites, since sulfur
  is not a greenhouse gas and stays emissions-driven.

---

## 4. Config walkthrough

### Time window

```yaml
time:
  historical_start_year: 1900
  future_start_year: 2015.0
  scenario_end_year: 2100
  extensions_end_year: 2500
```

`future_start_year: 2015` — not the ScenarioMIP-standard 2023 — is the
Frankenstein harmonisation year: the point from which the stitched fossil
trajectory replaces the native marker. `historical_start_year: 1900` is used for
column bookkeeping and plot baselining, not for the FaIR run, which always starts
at 1750.

### Flags

```yaml
flags:
  make_plots: True
  dump_csvs: True
  read_non_co2_from_csv: True
  read_afolu_from_csv: True
  regionalize_optimised_output: True
```

`read_non_co2_from_csv` and `read_afolu_from_csv` are the important ones. With
both `True`, 5191 does **not** run `do_all_non_co2_extensions` or
`calculate_afolu_extensions`. Instead it slices the already-extended series
straight out of the loaded input:

```python
df_all      = scenarios_complete_global.loc[~pix.ismatch(variable="**CO2**")]
afolu_dfs["linear_afolu_rampdown"] = scenarios_complete_global.loc[pix.ismatch(variable="**CO2|AFOLU**")]
```

So the input CSV must already carry non-CO2 and AFOLU across the full 1750–2500
window; FLEX only generates the *fossil* CO2 extension. This is the single
biggest behavioural difference between `vl-frankenstein` and
`scenariomip_default`, and it is why the `non_co2_targets` block below has no
effect in the current setup.

`regionalize_optimised_output` switches on the 5196 block that pushes the
optimised global fossil trajectory back down into sectors and regions (§5.3).

### Fossil CO2 storyline

```yaml
fossil_evolution:
  VL-fossil-frankenstein:
    type: ECS
    params: [2200, -3500.0, 2450, 2500, 20, 20]
```

`ECS` = *Exponential/linear → Constant → Sigmoid*, with
`[exp_end, exp_targ, sig_start, sig_end, roll_in, roll_out]`. Read as a story
about **total** CO2 (FFI + AFOLU):

| Phase | Years | Behaviour |
|---|---|---|
| Ramp | 2101 → 2200 | Smooth linear decline from the 2100 value to `exp_targ` = −3500 Mt CO2/yr, with the slope at 2100 matched by a spline derivative so there is no kink at the join |
| Hold | 2200 → 2450 | Net-negative plateau at −3500 Mt CO2/yr |
| Roll-off | 2450 → 2500 | Smooth return to zero, `roll_in`/`roll_out` = 20 yr |
| Zero | 2500 | 0 |

The 250-year net-negative plateau is the substantive assumption: sustained
large-scale CDR that draws CO2 back down over the extension period rather than
merely reaching net zero.

`exp_targ: null` would instead extrapolate a target from the late-scenario slope
via `get_exp_targ_from_current_data`; here it is prescribed.

The `-hold` marker carries the same block, explicitly marked `# initial guess;
optimized`. Its values are never used: 5191 skips optimised markers entirely, and
5196 rebuilds the trajectory from the optimiser's parameters.

### Removal strategy

```yaml
removal_strategy:
  VL-fossil-frankenstein: {type: NEG, params: [100, 60]}
```

The storyline sets *net* fossil CO2; the split into gross positive emissions and
gross removals is a separate decision.

- **`NEG`** — gross positive emissions decay on a prescribed timescale
  (`decay_timescale` = 100 yr, `offset` = 60 yr) and **CDR is the residual**
  needed to hit the net target. Appropriate when the net path is deeply
  negative: it lets removals grow to whatever the storyline demands rather than
  forcing gross emissions to go negative.
- **`POS`** — the mirror image: CDR held constant, gross positive adjusts.

Two vestigial entries remain from the WIEMIP-era naming convention:
`VL-fossil-frankenstein-CF` and `VL-fossil-frankenstein-zero-afolu-CF`. No such
markers exist any more (they were renamed `-hold`), so these are dead config.
They cause no harm — 5196 derives the strategy for a `-hold` marker from its
*base scenario*, looking up whichever markers in `scenario_model_match` also
appear in `removal_dictionary`, which resolves to `NEG` via
`VL-fossil-frankenstein`.

### Non-CO2 targets

```yaml
non_co2_targets:
  "Emissions|CH4":
    VL-fossil-frankenstein: 95.0
  "Emissions|Sulfur":
    VL-fossil-frankenstein: 20.0
```

The three-way semantics the loader supports:

- **A number** — extend to that 2500 endpoint with the default sigmoid
  (`sigmoid_shift` 40, `sigmoid_len` 50, branching at `scenario_end_year`). A dict
  form `{target, sigmoid_shift, sigmoid_len, branch_year}` gives full control.
- **`null`** — auto-derive the target from the data (original ScenarioMIP
  behaviour: `min(scenario minimum, first historical value)`).
- **Marker absent from a listed variable** — *skip the extension entirely* and
  follow the source scenario. This is how the `-hold` markers are made to share
  the base marker's CH4 and sulfur exactly, which is what makes the
  counterfactual a clean CO2-only comparison.

Note the caveat from §4 (Flags): with `read_non_co2_from_csv: True` this block is
not exercised at all. It documents intent and will take effect if that flag is
turned off.

### Forcing

```yaml
forcing_scenario:
  VL-fossil-frankenstein: VL
  VL-fossil-frankenstein-hold: VL
```

`volcanic_solar.csv` is keyed by the seven canonical ScenarioMIP IDs. Both
Frankenstein markers borrow `VL`'s volcanic/solar series. `setup_fair` and 5201
handle this by cloning the `VL` rows under the new scenario names into a
temporary forcing file. Solar forcing is then zeroed for every scenario
(`f.forcing.loc[dict(scenario=s, specie="Solar")] = 0`).

### Optimisation

```yaml
optimization:
  VL-fossil-frankenstein-hold:
    enabled: true
    target_year: peak
    departure_year: peak
    departure_offset: -15
    n_configs: 50
    optimize_params: [exp_targ, sig_start, sig_end]
    fixed_params: {}
    bounds:
      exp_targ:  [0.0, 5000.0]
      sig_start: [2030, 2170]
      sig_end:   [2100, 2250]
```

- `target_year: peak` — the temperature to hold is read off the *baseline* FaIR
  run at its own maximum, rather than being hard-coded. Robust to the input
  scenario changing.
- `departure_year: peak` with `departure_offset: -15` — branch 15 years *before*
  the peak. Branching exactly at the peak leaves no room to bend the trajectory
  without a discontinuity; 15 years gives the ramp somewhere to act.
- `n_configs: 50` — 50 climate configurations drawn evenly spaced from the
  ~1000-member calibrated-constrained set. Enough that the *median* temperature
  the objective targets is stable, cheap enough for ~15 generations of
  differential evolution.

---

## 5. What each pipeline step does

### 5.1 `5191_extension` — build the base extension

1. Load the Frankenstein global and regional CSVs plus standard history;
   coerce year columns to numerics; add a `workflow` index level if the regional
   file lacks one.
2. Apply `regional_scenario_fallback`, cloning regional/global rows for the
   `… Ref1p5 hold` scenario name.
3. Compute 2100 compositional fractions per `(model, scenario)` via
   `get_2100_compound_composition_co2` — three sets: all fossil sectors, CDR
   sectors only, and gross-positive sectors only. These fractions are what hold
   the sectoral and regional composition fixed through the extension.
4. Take non-CO2 and AFOLU straight from the input (see flags above).
5. For each non-optimised marker, run
   `process_single_scenario_storyline_wrapper` to apply the ECS storyline to
   total CO2 and back out fossil CO2 = total − AFOLU.
6. Call `regionalize_fossil_co2`, which encapsulates removal disaggregation, the
   gross-positive/CDR split under the `NEG` strategy, regional CDR fluxes,
   sectoral infill for missing regions, and the historical/future merge.
7. Write outputs, and convert the continuous IAMC timeseries into FaIR's format
   (`convert_continuous_to_fair_csv`): filter to `World`, map IAMC variable names
   to FaIR species, shift year columns by +0.5 to FaIR's mid-year timepoints, and
   map long scenario names back to marker short names.

Key output: `outputs/vl-frankenstein/emissions_1750-2500.csv`.

### 5.2 `5195_optimise` — solve for the hold trajectory

For `VL-fossil-frankenstein-hold`:

1. **Find the target.** Run FaIR on the source marker with 50 configs. Take
   `peak_year = argmax(median temperature)`, `target_temp` = median temperature
   at that year, `departure_year = peak_year − 15`.
2. **Clamp the search space.** `exp_targ`'s upper bound is lowered to the total
   CO2 at the departure year, so the counterfactual can never *jump up* at the
   branch. If the configured lower bound (0.0) now exceeds that ceiling — which it
   will, once VL's total CO2 has gone net-negative — the whole window slides down
   preserving its 5000 Mt width. This is why `[0.0, 5000.0]` in the YAML does not
   mean "positive emissions only" in practice.
3. **Optimise.** `scipy.optimize.differential_evolution` over
   `(exp_targ, sig_start, sig_end)`, `seed=42`, `maxiter=15`, `popsize=5`,
   `tol=0.01`, `atol=0.5`, `polish=True`, `vectorized=True`.

   `vectorized=True` is what makes this affordable: each generation's ~15
   candidates are written into **one** emissions CSV as 15 pseudo-scenarios and
   evaluated in a **single** FaIR call
   (`_batch_objective_plateau`), rather than 15 sequential model runs.

   Objective:

   ```
   cost = Σ_{t ≥ departure_year} ( median_temperature(t) − target_temp )²
   ```

   Candidates with `sig_start ≥ sig_end` are rejected with a `1e6` penalty, as is
   any FaIR failure.

4. Write `optimization_results.json` (parameters, target temperature, departure
   year, final cost, convergence flag).

Splitting the solve (5195) from its application (5196) means emissions can be
regenerated without paying for the optimisation again.

#### The trajectory the optimiser actually searches over

This is worth being precise about, because it is **not** the same shape as
5191's `ECS` storyline. `_build_co2_trajectory` in
[src/flex/optimise.py](../src/flex/optimise.py) — and the identical inline copy in
5196 — sets `exp_end = int(sig_start)` and then builds total CO2 as:

| Phase | Years | Behaviour |
|---|---|---|
| Ramp | `departure_year` → `sig_start` | Linear from the departure-year value to `exp_targ` |
| Hold | — | Degenerate: `exp_end == sig_start`, so the plateau branch is never reached |
| Roll-off | `sig_start` → `sig_end` | Smoothstep `s = 3t² − 2t³` from `exp_targ` to 0 |
| Zero | after `sig_end` | 0 |

Fossil CO2 is then recovered as `FFI = total − AFOLU` from the departure year
onward, leaving AFOLU untouched.

So the effective family is **ramp → smoothstep → zero**, a three-parameter shape,
with `exp_targ` acting as the level the ramp reaches at `sig_start` rather than a
sustained plateau. The optimiser's parameter names are inherited from the ECS
storyline vocabulary but their geometry differs — worth remembering when
comparing `-hold` against the base marker's genuinely-plateaued storyline.

### 5.3 `5196_apply_optimised` — materialise the counterfactual

1. Rebuild the optimised CO2 FFI trajectory from the JSON parameters (same
   construction as above) and splice it into the emissions CSV from the departure
   year onward under the new marker name, via `modify_emissions_csv`. All other
   species are copied verbatim from the source marker.
2. **Regionalise** (because `regionalize_optimised_output: True`). For each
   optimised marker: restrict the untouched regional/non-CO2/AFOLU inputs to the
   source `(model, scenario)`, wrap the optimised global fossil series in a
   `Emissions|CO2|Energy and Industrial Processes` frame, and push it back through
   the same `regionalize_fossil_co2` machinery 5191 uses. Then
   `rescale_fossil_splits_to_optimised` reconciles the sector/region breakdown to
   the optimised net EIP using the `NEG` strategy (removals absorb the delta),
   preserving each year's sector and region *shares*. Finally the scenario index
   level is relabelled from the shared long name to the marker name, so base and
   counterfactual are distinguishable in the output.
3. **Verify.** Run every scenario through FaIR at the same `n_configs: 50` and
   emit, per optimised marker, a three-panel figure (temperature vs. target,
   CO2 FFI, cumulative CO2 FFI) plus a summary table of mean/min/max/range of
   post-departure temperature against the target.

That verification table is the thing to read first after a run: a small `Range
(K)` is the actual evidence that the hold worked, and it is reported
independently of the optimiser's own cost.

### 5.4 `5201_extension_fair_simulations` — the production run

Same FaIR v2.2 setup, but `full_ensemble = True` by default, so the full ~1000
member calibrated-constrained ensemble is used rather than the optimiser's 50.
`ch4_method = "Thornhill2021"`, non-stochastic. Exports:

| File | Contents |
|---|---|
| `fair_temperature_1750-2500.csv` | median, p05, p95 per scenario |
| `fair_forcing_1750-2500.csv` | per species |
| `fair_forcing_sum_1750-2500.csv` | total ERF |
| `fair_concentration_ghgs_1750-2500.csv` | CO2, CH4, N2O |
| `fair_co2e_emissions_1750-2500.csv` | AR6 GWP100 mass-adjusted CO2e |
| `fair_temperature_ecdf_data.csv` | per-member 2100 / 2300 / max anomalies vs. 1850 |
| `fair_emissions_by_species.csv` | CO2 FFI, CO2 AFOLU, CH4, Sulfur |

### 5.5 `5202_extension_fair_plots` — figures

Reads only the CSVs from 5201 (no FaIR re-run) and writes PNG+PDF pairs to
`plots/vl-frankenstein/`: `temperature_emis`, `extensions` (8-panel diagnostic),
`temperature_ecdf`, and `cf_scenarios` (the counterfactual pair — total CO2 and
temperature side by side).

---

## 6. Outputs

In `outputs/vl-frankenstein/`:

| File | What it is |
|---|---|
| `emissions_1750-2500.csv` | FaIR-format global emissions, **including** the optimised `-hold` marker after 5196 |
| `extended_scenarios_1750_2500.csv` | IAMC-format extended scenarios, `stage="extended"`, internal diagnostic variables stripped |
| `continuous_emissions_timeseries_1750_2500.csv` | Merged historical + future, all variables |
| `extensions_full_emissions_timeseries_2023_2500.csv` | Full regional/sectoral breakdown |
| `extended_scenarios_optimised_1750_2500.csv` | World-level optimised counterfactual |
| `extensions_full_emissions_timeseries_optimised_2023_2500.csv` | Regional/sectoral optimised counterfactual — the file that actually carries the split |
| `optimization_results.json` | Solved parameters and diagnostics |
| `optimization_<marker>_verification.png` | 5196 verification figure |
| `fair_*.csv` | 5201 climate outputs |
| `notebooks/*.ipynb` | Rendered, fully-executed pipeline notebooks |

---

## 7. How the configuration got here

The config has been reshaped repeatedly as the experiment's question sharpened.
The trail, oldest first:

| Commit | Change | Why it matters |
|---|---|---|
| `ed44cb4`–`887b1ec` | Introduced as `vl-frankenstein-configs.yaml`, renamed to `vl-frankenstein.yaml` | Config name must match the `pixi run pipeline` argument |
| `8274a77` | Non-CO2 targets **removed** from the `-hold` markers | Established the "not listed ⇒ follow the source scenario" semantics, making the counterfactual CO2-only |
| `98da821` | Fixed `departure_year: 2030` → `peak` with `departure_offset: -15`; `sig_end` moved from fixed (2450) into the optimised set | Stopped hard-coding a branch year that would drift as inputs changed; three free parameters instead of two |
| `9c5ec56` | `n_configs` 10 → 50 | A 10-member median was too noisy for the objective to be smooth |
| `5a85f32` | Added `concentrations_file`; tightened bounds to `exp_targ [0, 5000]`, `sig_start [2030, 2170]`, `sig_end [2100, 2250]` | Concentration-driven non-CO2 made the problem cleanly CO2-only; the earlier `sig_end` ceiling of 3000 was outside the simulated period and wasted search effort |
| `6481e40` | Switched source scenario to `SSP1 - Very Low Emissions Ref1p5` and to the `VL_Ref1p5_260616.csv` delivery; commented out both zero-AFOLU markers; set `read_non_co2_from_csv` / `read_afolu_from_csv` to `True` | New input delivery arrived pre-extended, so FLEX now extends fossil CO2 only. Commit message records this round as *"unsuccessful"* |
| `20fbe88` | Added `regionalize_optimised_output: True` and the 5196 regionalisation block | The counterfactual was previously global-only; downstream users needed the sector/region split |

---

## 8. Reproducibility status — read before running

The config as committed on `vl-frankenstein-no-opt-annika-p2` **will not run in a
fresh checkout**. Three inputs the pipeline needs are absent:

1. **`src/flex/regionalize_fossil.py` is missing.** Both
   [notebooks/5191_extension.py:60](../notebooks/5191_extension.py#L60) and
   [notebooks/5196_apply_optimised.py:38-44](../notebooks/5196_apply_optimised.py#L38-L44)
   import from it (`regionalize_fossil_co2`, `build_global_fossil_extension_df`,
   `load_regionalization_inputs`, `rescale_fossil_splits_to_optimised`,
   `write_extended_scenarios_csv`). The module exists in no commit on any branch,
   and `src/` is not gitignored. It was factored out of 5191 in `20fbe88` — that
   commit removed 538 lines from the notebook — but the new file was never added.
   The pipeline fails at import in step 5191.

2. **`data/vl-extensions-inputs/VL_Ref1p5_260616.csv` is missing.** Only the
   earlier-generation files are present (`VL_frankenstein-full.csv`,
   `VL_frankenstein_AFOLU-full.csv`, `VL_frankenstein-FFCO2-sector_region.csv`,
   …), which carry the older scenario name `SSP1 - Very Low Emissions fossil
   frankenstein` and end at 2100 (2090 for the regional file). They are not
   drop-in substitutes: the current config's scenario names would not match, and
   with `read_non_co2_from_csv: True` the non-CO2 and AFOLU series would stop at
   2100 rather than reaching 2500.

3. **`data/fair-inputs/concentrations_1750-2500.csv` is missing.** Referenced by
   `concentrations_file`. `_fill_concentrations_from_file` would fail on open.

To recover a runnable state you need, in order: the `regionalize_fossil` module
(from whoever performed the `20fbe88` refactor), the `VL_Ref1p5_260616` delivery,
and the concentrations file. Failing that, checking out `5a85f32` gives a config
whose data dependencies are all present in the repository, at the cost of the
regionalised optimised output.

Smaller issues worth cleaning up when the above is resolved:

- `scenarios_global` lists the same file twice, duplicating every global row
  (§3).
- `removal_strategy` still carries dead `-CF` entries from the WIEMIP naming
  convention (§4).
- The comment `# NEG: [type, decbay_timescale, offset]` has a typo for
  `decay_timescale`, introduced in `6481e40`.
- `optimise.py:63` sets `no_scenario = True` inside the fallback branch of
  `_fill_concentrations_from_file` and never clears it, so a scenario matched by
  the loop still raises. It only triggers on the fallback path.
