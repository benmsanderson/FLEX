# The `WIEMIP` experiment

How the WIEMIP ensemble is built, why each configuration choice was made, and what
the pipeline actually does when you run it.

```bash
pixi run pipeline WIEMIP -- --parallel 3
```

Config: [configs/WIEMIP.yaml](../configs/WIEMIP.yaml)
Companion: [The `vl-frankenstein` experiment](vl-frankenstein-experiment.md)

---

## 1. What the experiment is

WIEMIP is the **full ScenarioMIP marker set plus three temperature-hold
counterfactuals**. It is the closest thing FLEX has to a production ensemble: all
seven markers (VL through HL) extended to 2500 with the standard storyline
machinery, and three of them paired with a `-CF` twin whose post-branch CO2 is
*solved for* rather than prescribed.

Each `-CF` scenario answers the same question at a different point on the warming
range: **what CO2 pathway would be needed to stop warming here, and hold it?**
The optimiser adjusts fossil CO2 so FaIR's median temperature stays flat at the
scenario's own peak level all the way to 2500. Because the three pairs span a very
low, a medium-low, and a high-overshoot pathway, the ensemble brackets the
carbon-budget cost of stabilisation across the plausible range.

WIEMIP began as a literal copy of `scenariomip_default.yaml` — git records the
copy at `45b2f19`, similarity 60% — with counterfactual markers layered on. The
seven baseline markers are unchanged from the default config apart from the `ML`
plot colour.

### Markers

| Marker | Scenario | Model | Colour | CO2 set by |
|---|---|---|---|---|
| `VL` | SSP1 - Very Low Emissions | REMIND-MAgPIE 3.5-4.11 | `#16188F` | Prescribed ECS storyline |
| `VL-CF` | *(same)* | *(same)* | `#16188F` | **Optimised** |
| `LN` | SSP2 - Low Overshoot_a | AIM 3.0 | `#22e5db` | Prescribed ECS |
| `L` | SSP2 - Low Emissions | MESSAGEix-GLOBIOM-GAINS 2.1-M-R12 | `#20A359` | Prescribed ECS |
| `ML` | SSP2 - Medium-Low Emissions | COFFEE 1.6 | `#916326` | Prescribed ECS |
| `ML-CF` | *(same)* | *(same)* | `#916326` | **Optimised** |
| `M` | SSP2 - Medium Emissions | IMAGE 3.4 | `#fc7b03` | Prescribed CS |
| `H` | SSP3 - High Emissions | GCAM 8s | `#a41212` | Prescribed ECS |
| `HL` | SSP5 - Medium-Low Emissions_a | WITCH 6.0 | `#E744F6` | Prescribed ECS |
| `HL-CF` | *(same)* | *(same)* | `#FF6600` | **Optimised** |

`VL-CF` and `ML-CF` reuse their source marker's colour; `HL-CF` keeps a distinct
orange from when it was the only counterfactual. Which of these matters depends on
the figure: 5202's Plots 1–3 colour each marker by its own `meta[2]`, so `HL-CF`
appears in orange there, while Plot 4 (`cf_scenarios`) colours *both* members of a
pair by the **source** marker's colour and distinguishes the counterfactual by a
dashed linestyle — so `HL-CF`'s own colour is ignored in that one.

**Ordering in `scenario_model_match` is load-bearing.** `FlexConfig.scenario_mapping`
walks the dict in order, records the first marker per `(scenario, model)` key, and
maps later collisions onto it. Because `VL` precedes `VL-CF`, `ML` precedes
`ML-CF`, and `HL` precedes `HL-CF`, this yields
`{VL-CF: VL, ML-CF: ML, HL-CF: HL}` — which is how 5195/5196 discover each
counterfactual's *source marker*, and how the CF scenarios inherit volcanic/solar
forcing (their names do not exist in `volcanic_solar.csv`). Reversing any pair
would invert the relationship silently.

---

## 2. Running it

```bash
pixi install
git lfs pull                      # the standard data CSVs are LFS-tracked
pixi run pipeline WIEMIP -- --parallel 3
```

The config has an `optimization` section, so `run_pipeline.py` executes all five
steps:

```
5191_extension  →  5195_optimise  →  5196_apply_optimised
                →  5201_extension_fair_simulations  →  5202_extension_fair_plots
```

`--parallel 3` is the natural setting: three independent optimisation targets, one
worker each. This is the config `PARALLEL_OPTIMIZATION.md` was written for, and
the only one in the repo where scenario-level parallelism actually buys anything —
5195 only spawns joblib workers when `len(markers_to_optimize) > 1`.

```bash
pixi run pipeline WIEMIP -- --parallel -1   # all cores, capped at 20
pixi run pipeline WIEMIP -- --parallel 50   # explicit override of the cap
pixi run pipeline WIEMIP -- --from 5196     # reuse existing optimisation results
pixi run pipeline WIEMIP -- --only 5195 --parallel 3
```

There are three nested levels of parallelism, worth keeping straight:

| Level | Mechanism | Controlled by |
|---|---|---|
| Scenario | joblib, 3 optimisations at once | `--parallel N` |
| Candidate | `differential_evolution(vectorized=True)` evaluates a whole generation in **one** FaIR call | `popsize` (5) in `optimise.py` |
| Ensemble | FaIR runs many climate configs per call | `n_configs: 50` in the YAML |

Note that `PARALLEL_OPTIMIZATION.md` is now stale on two points: it states
`n_configs=1` during optimisation and `memory_limited=True` (5-member ensemble).
The config sets `n_configs: 50`, and when `n_configs` is set it overrides
`memory_limited` and draws evenly spaced members from the full ~1000-member
calibrated set. Budget accordingly.

---

## 3. Input data

WIEMIP has **no `data_sources` block**, so it uses the repository's standard
inputs:

| File | Size | Contents |
|---|---|---|
| `data/scenarios_complete_global.csv` | ~8 MB | Global marker scenarios, 1750–2100 |
| `data/scenarios_regional.csv` | ~320 MB | Regional scenarios |
| `data/history.csv` | ~192 KB | Historical global emissions |
| `data/history_regional.csv` | ~160 MB | Historical regional emissions |

All four are Git LFS pointers in a fresh clone. `git lfs pull` before the first
run or 5191 will fail parsing a pointer file as CSV.

There is also **no `concentrations_file`**, so FaIR runs fully emissions-driven —
a substantive difference from `vl-frankenstein`, which prescribes non-CO2 GHG
concentrations. In WIEMIP the optimiser's CO2 perturbation still propagates into
CH4 lifetime (`ch4_method = "Thornhill2021"`) and the other emissions-driven GHGs,
so a `-CF` solution here is a full-Earth-system answer rather than a pure
carbon-budget one.

And **no `forcing_scenario` block**, so the volcanic/solar mapping is exactly
`cfg.scenario_mapping` — the CF-to-source relationship described above.

---

## 4. Config walkthrough

### Time window

```yaml
time:
  historical_start_year: 1900
  future_start_year: 2023.0
  scenario_end_year: 2100
  extensions_end_year: 2500
```

Standard ScenarioMIP values. (`vl-frankenstein` moves `future_start_year` to 2015
for its harmonisation; WIEMIP does not.)

### Flags

```yaml
flags:
  make_plots: false
  dump_csvs: true
```

Both `read_non_co2_from_csv` and `read_afolu_from_csv` are **absent**, so they
default to `False`, meaning 5191 is expected to *generate* the non-CO2 and AFOLU
extensions itself rather than read them pre-extended from the input. See §7 — this
is the flag combination that the current branch broke.

### Fossil CO2 storylines — the seven baseline markers

Total CO2 (FFI + AFOLU) evolves through prescribed phases. `ECS` takes
`[exp_end, exp_targ, sig_start, sig_end, roll_in, roll_out]`; `CS` takes
`[stop_const, end_sig, roll_in, roll_out]`.

| Marker | Type | Ramp to | by | Hold until | Zero by | Story |
|---|---|---|---|---|---|---|
| `VL` | ECS | −3500 | 2200 | 2450 | 2500 | Modest, very long net-negative plateau |
| `LN` | ECS | −24000 | 2120 | 2200 | 2300 | Deep, fast net-negative — the overshoot must be clawed back |
| `L` | ECS | *auto* | 2160 | 2160 | 2260 | `exp_targ: null` ⇒ target extrapolated from the late-scenario slope |
| `ML` | ECS | −13000 | 2150 | 2230 | 2300 | Intermediate CDR |
| `M` | CS | — | — | — | 2240 | `stop_const == scenario_end`, so the constant phase is empty: declines directly from the 2100 value to zero |
| `H` | ECS | *auto* | 2150 | 2175 | 2300 | Slope-extrapolated, no imposed CDR |
| `HL` | ECS | −22000 | 2150 | 2200 | 2300 | Deep net-negative to unwind a high overshoot |

`exp_targ: null` routes through `get_exp_targ_from_current_data`, which takes a
spline derivative at the end of the scenario and extrapolates a fraction (10%) of
the way along — a "keep doing roughly what you were doing" default, used for the
two markers (`L`, `H`) where no strong CDR narrative was wanted.

The joins are not naive splices: `make_linear_function_with_smooth_transition`
matches the slope at 2100 with a spline derivative and blends over `roll_in` /
`roll_out` years, so there is no kink where the storyline takes over.

### Fossil CO2 storylines — the `-CF` markers

```yaml
  VL-CF: {type: ECS, params: [2048, 3300, 2048, 2450, 20, 20]}
  ML-CF: {type: ECS, params: [2092, 2000, 2092, 3200, 20, 20]}
  HL-CF: {type: ECS, params: [2125, 6200, 2125, 2290, 20, 20]}
```

**These are never applied.** 5191 processes `scenario_model_match` *minus*
everything in `cfg.optimization`:

```python
scenario_model_match = {k: v for k, v in cfg.scenario_model_match.items()
                        if k not in cfg.optimization}
```

All three CF markers are optimisation targets, so 5191 skips them entirely and
5196 rebuilds their trajectories from the solved parameters instead.

They are worth reading anyway, because they are a **record of a solved answer**.
Commit `88411f4` introduced them as round placeholders
(`[2050, 0, 2100, 2300, …]`); `9c5ec56` replaced them with the values above. Note
that in every one `exp_end == sig_start` — exactly the relationship the optimiser
enforces internally (`exp_end = int(sig_start)`). These are optimiser outputs
written back into the config for the record, not inputs.

### Removal strategy

The storyline fixes *net* CO2; the gross-positive / CDR split is a separate
decision.

| Strategy | Markers | Behaviour |
|---|---|---|
| `NEG` | `VL` `[100, 60]`, `LN` `[50, 100]`, `L` `[50, 50]`, `ML` `[100, 0]`, `HL` `[80, 20]` | Gross positive emissions decay on the given `[decay_timescale, offset]`; **CDR is the residual** needed to hit the net target |
| `POS` | `M`, `H` | CDR held constant; gross positive adjusts to follow the net path |

`NEG` is used wherever the net path goes deeply negative — it lets removals grow
to whatever the storyline demands instead of forcing gross emissions below zero.
`M` and `H` never go net-negative, so `POS` is the natural reading: continued CDR
at its 2100 level, with the decline coming from gross emissions.

The decay parameters vary by marker because the pathways get to net zero at very
different dates: `LN` `[50, 100]` decays fast but starts late; `ML` `[100, 0]`
decays slowly from the outset. Each CF marker copies its source's strategy
exactly, so the split logic is not a confounder in the comparison.

### Non-CO2 targets

```yaml
non_co2_targets:
  "Emissions|CH4":
    VL: 95.0    LN: 150.0   L: 95.0    ML: 120.0
    M: 450.0    H: 520.0    HL: 110.0
    HL-CF: {target: 200.0, branch_year: 2080}
  "Emissions|Sulfur":
    VL: 20.0    LN: 10.0    L: null    ML: 20.0
    M: 20.0     H: 50.0     HL: 10.0
    HL-CF: {target: 10.0, branch_year: 2080}
```

The loader's three-way semantics: a **number** means "sigmoid to that 2500
endpoint" with defaults (`sigmoid_shift` 40, `sigmoid_len` 50, branching at
`scenario_end_year`); a **dict** gives full control over shift, length and branch
year; **`null`** auto-derives the target from the data (`min(scenario minimum,
first historical value)` — original ScenarioMIP behaviour, used here for `L`'s
sulfur); and a marker **absent** from a listed variable skips the extension
entirely and follows the source scenario.

Targets track the socioeconomic story rather than the CO2 path: `M` and `H` hold
CH4 near 450–520 Mt/yr (persistent agricultural and fossil methane), while the
mitigation pathways converge to 95–150.

The `HL-CF` dict entries — added in `8274a77`, which is also the commit that
introduced the dict form to the loader — express the intent that the
counterfactual should branch its non-CO2 at 2080 too, toward a *less* ambitious
CH4 endpoint (200 vs. HL's 110). **On the current code path they are dead**, for
two independent reasons: `HL-CF` is filtered out of 5191 as an optimisation
target, and 5196 builds the counterfactual with `modify_emissions_csv`, which
copies every species verbatim from the source marker and replaces only `CO2 FFI`.

The practical consequence is worth stating plainly: **all three counterfactuals
are pure CO2 perturbations.** Their CH4, sulfur, and everything else are identical
to their source markers. That is arguably the cleaner experiment, but it is not
what the `HL-CF` non-CO2 block says, and the two should be reconciled.

### Optimisation

```yaml
optimization:
  HL-CF: {target_year: peak, departure_year: 2073, departure_offset: -15, n_configs: 50,
          optimize_params: [exp_targ, sig_start, sig_end],
          bounds: {exp_targ: [5000, 15000], sig_start: [2100, 2200], sig_end: [2100, 3000]}}
  ML-CF: {… departure_year: 2060, bounds: {exp_targ: [-10000, 5000], sig_start: [2040, 2200], …}}
  VL-CF: {… departure_year: peak,  bounds: {exp_targ: [-5000, 5000],  sig_start: [2040, 2200], …}}
```

| Marker | `target_year` | `departure_year` | Effective branch | `exp_targ` bounds |
|---|---|---|---|---|
| `VL-CF` | peak | `peak` | peak − 15 | [−5000, 5000] |
| `ML-CF` | peak | `2060` | **2045** | [−10000, 5000] |
| `HL-CF` | peak | `2073` | **2058** | [5000, 15000] |

`departure_offset: -15` applies to *both* forms — `int(departure_year_cfg) +
departure_offset` — so the literal years are offsets too, not final answers. The
config header comment and `description` still say HL-CF "departs from the HL
pathway at 2080"; the effective branch is 2058.

Design choices worth naming:

- **`target_year: peak` everywhere.** The temperature to hold is read off the
  scenario's own baseline FaIR run at its maximum, not hard-coded. This survives
  changes to the input data.
- **Branch 15 years before the peak.** Branching exactly at the peak leaves no room
  to bend the trajectory without a discontinuity.
- **`departure_year` literal for `ML-CF` and `HL-CF`.** `9c5ec56` changed both from
  `peak` to fixed years while leaving `VL-CF` on `peak`. For flat-topped pathways
  the argmax of a median temperature curve is numerically unstable — a small
  ensemble change can move it decades — so the two broader-peaked scenarios got
  pinned. `VL`, which peaks sharply, did not need it.
- **`exp_targ` bounds are ordered by scenario.** `HL-CF` searches only positive
  values (5000–15000): holding temperature on a high pathway from 2058 does not
  require net-negative CO2, just a much slower decline. `VL-CF`'s window straddles
  zero. `ML-CF`'s reaches deeply negative. The windows encode a prior about what
  each answer should look like.
- **`n_configs: 50`** — enough that the *median* the objective targets is stable
  across generations, cheap enough for ~15 generations of differential evolution.
  Raised from 10 in `9c5ec56`.

---

## 5. What the pipeline does

### 5.1 `5191_extension`

Loads the standard global/regional scenarios and history, computes 2100
compositional fractions per `(model, scenario)` (all fossil sectors, CDR sectors,
gross-positive sectors), generates non-CO2 and AFOLU extensions, applies each
marker's storyline to total CO2 and backs out fossil = total − AFOLU, then
disaggregates removals, splits gross-positive/CDR per the removal strategy,
infills missing regions, and merges historical with future.

Runs for the **seven baseline markers only** — the CF markers are excluded.

Emits `outputs/WIEMIP/emissions_1750-2500.csv` (FaIR format: World only, IAMC
variable names mapped to FaIR species, year columns shifted +0.5 to FaIR's
mid-year timepoints).

### 5.2 `5195_optimise`

For each of `HL-CF`, `ML-CF`, `VL-CF` — in parallel under `--parallel 3`:

1. **Find the target.** Run FaIR on the source marker with 50 configs. Take
   `peak_year = argmax(median temperature)`, `target_temp` at `target_year`, and
   `departure_year` per the table above.
2. **Clamp the search space.** `exp_targ`'s ceiling is lowered to the
   departure-year total CO2, so a counterfactual can never *jump up* at the
   branch. If the configured floor then exceeds the ceiling, the whole window
   slides down preserving its width. This is why `HL-CF`'s `[5000, 15000]` does
   not mean the answer will land in that range — it means "start looking there,
   but never above the branch-year value".
3. **Optimise** `(exp_targ, sig_start, sig_end)` with
   `scipy.optimize.differential_evolution`: `seed=42`, `maxiter=15`, `popsize=5`,
   `tol=0.01`, `atol=0.5`, `polish=True`, `vectorized=True`. Each generation's
   ~15 candidates are written into one emissions CSV as pseudo-scenarios and
   evaluated in a **single** FaIR call.

   ```
   cost = Σ_{t ≥ departure_year} ( median_temperature(t) − target_temp )²
   ```

   `sig_start ≥ sig_end` and FaIR failures return a `1e6` penalty.
4. Write `optimization_results.json`.

#### The trajectory family being searched

Not the same shape as the `ECS` storyline, despite the shared parameter names.
`_build_co2_trajectory` in [src/flex/optimise.py](../src/flex/optimise.py) sets
`exp_end = int(sig_start)`, so total CO2 is:

| Phase | Years | Behaviour |
|---|---|---|
| Ramp | branch → `sig_start` | Linear from the branch-year value to `exp_targ` |
| Hold | — | Degenerate: `exp_end == sig_start`, never reached |
| Roll-off | `sig_start` → `sig_end` | Smoothstep `s = 3t² − 2t³` from `exp_targ` to 0 |
| Zero | after `sig_end` | 0 |

Fossil CO2 is then `FFI = total − AFOLU` from the branch year onward, AFOLU
untouched. The effective family is **ramp → smoothstep → zero**: `exp_targ` is the
level reached at `sig_start`, not a sustained plateau. Keep this in mind when
comparing a `-CF` against its source marker's genuinely-plateaued storyline.

Note also that `sig_end`'s upper bound of 3000 lies well outside the simulated
period (2500). A solution with `sig_end > 2500` means "still ramping down at the
end of the run" — legitimate, but it makes the reported `sig_end` uninterpretable
as a zero-crossing date.

### 5.3 `5196_apply_optimised`

Rebuilds each trajectory from the JSON parameters and splices it into the
emissions CSV from the branch year onward under the CF name, copying all other
species verbatim from the source marker. Then runs every scenario through FaIR at
the same `n_configs: 50` and emits, per CF marker, a three-panel verification
figure (temperature vs. target, CO2 FFI, cumulative CO2 FFI) plus a summary table
of mean/min/max/range of post-departure temperature against the target.

That table is the thing to read first after a run: a small `Range (K)` is the
actual evidence the hold worked, reported independently of the optimiser's cost.

WIEMIP does **not** set `regionalize_optimised_output`, so the CF scenarios stay
global-only. (`vl-frankenstein` turns this on; see that document's §5.3.)

### 5.4 `5201_extension_fair_simulations`

Production FaIR v2.2 run over all ten scenarios with `full_ensemble = True` — the
full ~1000-member calibrated-constrained set, not the optimiser's 50.
Non-stochastic, solar forcing zeroed. Exports temperature (median/p05/p95),
forcing by species and total ERF, CO2/CH4/N2O concentrations, AR6 GWP100 CO2e, and
per-member ECDF data for 2100 / 2300 / peak anomalies.

### 5.5 `5202_extension_fair_plots`

Reads only the 5201 CSVs. Writes PNG+PDF pairs to `plots/WIEMIP/`:
`temperature_emis`, `extensions` (8-panel diagnostic), `temperature_ecdf`, and
`cf_scenarios`.

Two things about `cf_scenarios` (Plot 4) are WIEMIP-specific:

- It builds its pairs as `[(s.replace("-CF", ""), s) for s in results if
  s.endswith("-CF")]`. The `-CF` suffix is therefore **functional, not
  cosmetic** — it is the string that pairs a counterfactual with its source.
  `vl-frankenstein`'s `-hold` markers do not match, so that config never produces
  this figure.
- It prefers `optimization_results_handtuned.json` over
  `optimization_results.json` when the former exists. This is a deliberate manual
  override: it lets a hand-adjusted parameter set drive the published figure
  without touching the optimiser's own output. Nothing else in the pipeline reads
  that file, so a hand-tuned figure can silently disagree with the emissions in
  `emissions_1750-2500.csv`. Check which file exists before trusting the plot.

---

## 6. How the configuration got here

| Commit | Change | Why |
|---|---|---|
| `45b2f19` | Copied from `scenariomip_default.yaml`; added `HL-CF` and the first `optimization` block (`departure_year: 2080`, `optimize_params: [exp_targ, sig_start]`, `sig_end` fixed at 2300, `n_configs: 1`) | First counterfactual, minimal free parameters |
| `e698a48` | Dropped the redundant `plot_colors` block; replaced `tab:*` names with the ScenarioMIP hex palette | Colour lived in two places; `scenario_model_match` won |
| `aeee8b7` | Added explicit `n_configs: 1` | Made the ensemble size visible rather than defaulted |
| `8274a77` | `HL-CF` non-CO2 targets promoted from bare numbers to dicts with `branch_year: 2080`; loader gained the dict form and the "not listed ⇒ follow source" rule | Intent was a 2080 non-CO2 branch for the counterfactual (never took effect — §4) |
| `88411f4` | Added `ML-CF` and `VL-CF` with placeholder storylines and their own optimisation blocks | Extended the experiment from one counterfactual to three, spanning the warming range |
| `86d0dfc` | `exp_targ` bounds for `ML-CF`/`VL-CF` widened from `[5000, 15000]` to `[-10000, 10000]` | The high-pathway window was wrong for low pathways — those need net-negative CO2 to hold |
| `14fd105` | `target_year: peak`, `departure_offset: -15`; `sig_end` moved from fixed (2300) into the optimised set; `n_configs` 1 → 10; per-scenario bounds tightened; the stale `objective: plateau_at_departure` key dropped | Stopped hard-coding branch years; three free parameters instead of two; the objective key was never read by the loader |
| `9c5ec56` | `n_configs` 10 → 50; `ML-CF`/`HL-CF` `departure_year` pinned to 2060/2073; `-CF` storyline params replaced with solved values; `ML` colour `#dec820` → `#916326` | A 10-member median was too noisy; flat-topped peaks made `argmax` unstable; yellow was illegible on white |

---

## 7. Reproducibility status — read before running

**On the current branch (`vl-frankenstein-no-opt-annika-p2`), WIEMIP will not
run.** Two independent blockers, both introduced while reworking the pipeline for
the Frankenstein config:

1. **`src/flex/regionalize_fossil.py` is missing.**
   [notebooks/5191_extension.py:60](../notebooks/5191_extension.py#L60) imports
   `regionalize_fossil_co2` from it. The module exists in no commit on any
   branch — it was factored out of 5191 in `20fbe88` (which removed 538 lines from
   the notebook) but never added. 5191 fails at import, for every config.

2. **The non-CO2 / AFOLU generation path is disabled.** `6481e40` changed
   `do_and_write_to_csv` from `True` to a hardcoded `False` and restructured the
   branch:

   ```python
   do_and_write_to_csv = False
   if read_non_co2_from_csv:        # False for WIEMIP — not set in the config
       df_all = scenarios_complete_global.loc[~pix.ismatch(variable="**CO2**")]
   elif do_and_write_to_csv:        # hardcoded False
       df_all = do_all_non_co2_extensions(scenarios_complete_global, history)
   else:                            # WIEMIP lands here
       df_all = pd.read_csv("first_draft_extended_nonCO2_all.csv", …)
   ```

   WIEMIP falls through to the cached-CSV branch, which reads
   `first_draft_extended_nonCO2_all.csv` and globs
   `first_draft_extended_afolu_linear*.csv` **relative to the process working
   directory**. Those files are gitignored and absent; the AFOLU glob returns
   nothing, leaving `afolu_dfs = {}` and a `KeyError` on
   `afolu_dfs["linear_afolu_rampdown"]`.

   That change was made so the Frankenstein config could consume a pre-extended
   input. It has the side effect that no config can generate its own non-CO2
   extensions any more.

**`5a85f32` is the last commit where WIEMIP's path through 5191 is intact** —
`do_and_write_to_csv = True`, no `regionalize_fossil` dependency, and the WIEMIP
config already in its `9c5ec56` form. Check it out to reproduce the ensemble as
last run.

To fix forward rather than back: restore `regionalize_fossil.py` from whoever
performed the `20fbe88` refactor, and make the non-CO2 / AFOLU generation
reachable — most cleanly by promoting `do_and_write_to_csv` to a config flag
alongside `read_non_co2_from_csv` rather than leaving it hardcoded in the
notebook.

Note also that `configs/WIEMIP.yaml` does not exist on `main` at all; `main`
predates the YAML-config infrastructure entirely and this branch is 38 commits
ahead of it. There is no upstream version to diff against.

Smaller items worth cleaning up:

- The config header comment describes "a counterfactual **LN** scenario (LN-CF)"
  and the `description` says HL-CF "departs from the HL pathway at 2080". Neither
  is true: there is no LN-CF, and HL-CF's effective branch is 2058.
- `HL-CF`'s `non_co2_targets` entries are dead config (§4) — either wire them into
  5196 or drop them, but they should not read as active.
- The `-CF` `fossil_evolution` blocks are records of solved answers, not inputs; a
  comment saying so would prevent someone tuning them expecting an effect.
- `sig_end` upper bounds of 3000 exceed the 2500 simulation horizon (§5.2).
- `PARALLEL_OPTIMIZATION.md` still documents `n_configs: 1` and a 5-member
  `memory_limited` ensemble during optimisation; both were superseded by
  `n_configs: 50`.
