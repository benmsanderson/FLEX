---
marp: true
theme: default
paginate: true
backgroundColor: white
style: |
  section {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 22px;
    padding: 40px 50px;
  }
  h1 { font-size: 40px; color: #1a2e5a; }
  h2 { font-size: 30px; color: #1a2e5a; border-bottom: 2px solid #1a2e5a; padding-bottom: 6px; }
  h3 { font-size: 24px; color: #2c5282; }
  .title-slide h1 { font-size: 44px; }
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
  .columns3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
  .highlight { background: #eef2ff; border-left: 4px solid #1a2e5a; padding: 12px 16px; border-radius: 4px; }
  .scenario-vl  { color: #16188F; font-weight: bold; }
  .scenario-ln  { color: #0ea5a0; font-weight: bold; }
  .scenario-l   { color: #20A359; font-weight: bold; }
  .scenario-ml  { color: #a89000; font-weight: bold; }
  .scenario-m   { color: #fc7b03; font-weight: bold; }
  .scenario-h   { color: #a41212; font-weight: bold; }
  .scenario-hl  { color: #9b15b3; font-weight: bold; }
  .small { font-size: 16px; color: #555; }
  .fig-placeholder {
    background: #f0f4ff;
    border: 2px dashed #8899cc;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    color: #445;
    font-style: italic;
    min-height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  img { max-width: 100%; max-height: 380px; object-fit: contain; }
  footer { font-size: 14px; color: #888; }
---

<!-- _class: title-slide -->
<!-- _paginate: false -->

# Overview of Global Scenarios and ScenarioMIP CMIP7

**Benjamin Sanderson**
CICERO Center for International Climate Research, Oslo

*Geoscientific Model Development, 2024–2026*

---

## Outline

1. **Why scenarios?** — role in climate science, history of scenario frameworks
2. **CMIP7 context** — the coupled model intercomparison project, Fast Track
3. **The case for emissions-driven projections**
4. **flat10MIP** — diagnosing carbon cycle responses
5. **ScenarioMIP-CMIP7** — the seven marker scenarios and their narratives
6. **Extensions beyond 2100** — the FLEX methodology
   - CO₂ storylines, non-CO₂ gases, CDR disaggregation
7. **Counterfactuals with FLEX** — WIEMIP and beyond
8. **Summary**

---

## The Role of Scenarios in Climate Science

Scenarios bridge **human choices** and **physical climate outcomes**

<div class="columns">
<div>

**What scenarios do:**
- Translate socioeconomic/policy assumptions into emissions trajectories
- Force Earth system models to generate consistent climate projections
- Enable risk assessment and impact research
- Inform IPCC assessment cycles

**Who uses them:**
- Climate modelling centres (CMIP)
- Impact assessment researchers (ISIMIP)
- Policy advisors (IPCC AR6/AR7)

</div>
<div class="fig-placeholder">

[FIG: Schematic of scenario workflow: IAM → emissions → ESM → impacts]
*(to be generated)*

</div>
</div>

---

## A Brief History of Scenario Frameworks

| Era | Scenario set | Driving metric | CMIP phase |
|-----|-------------|---------------|-----------|
| 1990s | SRES | Emissions | CMIP3 |
| 2010s | RCPs | Radiative forcing | CMIP5 |
| 2020s | SSPs + RCPs | Emissions + forcing | CMIP6 |
| 2025+ | SSPs (revised) | **Emissions** | **CMIP7** |

**Key shift in CMIP7:** move toward emissions-driven simulations as the primary protocol — enabling interactive carbon cycle feedbacks

<div class="highlight">

"Previous phases of CMIP have primarily focused on simulations driven by atmospheric concentrations of greenhouse gases. We argue that although concentration-driven simulations have advantages, emissions-driven simulations better represent the policy-relevant question."
*(Sanderson et al., 2024, GMD)*

</div>

---

## CMIP7 and the Fast Track

**Dunne et al. (2025)** — *An evolving CMIP7 and Fast Track in support of future climate assessment*

<div class="columns">
<div>

**CMIP7 goals:**
- Inform IPCC AR7 (2029)
- Prioritise policy-relevant questions
- Improve accessibility and reproducibility
- Reduce barriers for Global South participation

**Fast Track:**
- Smaller, targeted set of priority experiments
- Results available for AR7
- Includes DECK + ScenarioMIP

</div>
<div class="fig-placeholder">

[FIG: CMIP7 experiment hierarchy / Fast Track schematic]
*(from gmd-18-6671-2025, Fig. 1 or similar)*

</div>
</div>

---

## Why Emissions-Driven Simulations?

**Sanderson et al. (2024)** — *The need for carbon-emissions-driven climate projections in CMIP7*

<div class="columns">
<div>

**Problem with concentration-driven:**
- Locks in CO₂ pathway regardless of carbon cycle
- Different models have different carbon budgets for same concentrations
- Cannot assess feedbacks that alter the emissions–concentration relationship
- Misrepresents policy question: *we control emissions, not concentrations*

**Benefits of emissions-driven:**
- Carbon cycle uncertainty propagates correctly
- Cross-model comparison is fair (same emissions → different concentrations)
- Compatible with carbon budget frameworks

</div>
<div class="fig-placeholder">

[FIG: Schematic contrasting concentration-driven vs emissions-driven pathways; carbon cycle feedback loop]
*(from gmd-17-8141-2024)*

</div>
</div>

---

## flat10MIP: Diagnosing Carbon Cycle Responses

**Sanderson et al. (2025)** — *flat10MIP: an emissions-driven experiment to diagnose the climate response to positive, zero and negative CO₂ emissions*

<div class="columns">
<div>

**Motivation:**
- The proportionality between temperature and cumulative CO₂ (TCRE) underpins carbon budgets
- Deviations could affect net-zero timing estimates
- Carbon cycle asymmetry: is the response to negative emissions reversible?

**Experiment design:**
- Flat-10 Gt CO₂/yr emissions for 50 years, then ramp to zero, then negative
- All ESMs run with identical emissions forcing
- Isolates TCRE, reversibility, and asymmetry

</div>
<div class="fig-placeholder">

[FIG: flat10MIP prescribed emissions trajectory]
*(from gmd-18-5699-2025, Fig. 1)*

</div>
</div>

---

## flat10MIP: Key Science Questions

<div class="columns">
<div>

**Questions addressed:**
1. How does temperature respond symmetrically to positive vs. negative emissions?
2. What is the spread in TCRE across CMIP7 ESMs?
3. Does the ocean/land carbon sink behave differently under net-negative emissions?
4. How long does the climate system take to recover?

**Relevance for ScenarioMIP:**
- Informs interpretation of overshoot scenarios (LN)
- Constrains post-peak temperature behaviour in extensions

</div>
<div class="fig-placeholder">

[FIG: Multi-model temperature response to flat10 emissions — positive and negative phases]
*(from gmd-18-5699-2025)*

</div>
</div>

---

<!-- _class: section-header -->

## Part II: ScenarioMIP-CMIP7

---

## ScenarioMIP-CMIP7 Overview

**Van Vuuren et al. (2026)** — *The Scenario Model Intercomparison Project for CMIP7 (ScenarioMIP-CMIP7)*

<div class="highlight">

Scenarios serve as a critical tool in climate change analysis, enabling exploration of future evolution of the climate system, climate impacts, and the human system (including mitigation and adaptation actions).

</div>

**Seven marker scenarios** from Integrated Assessment Models (IAMs):
- Span a range from aggressive mitigation to high-emissions futures
- Each grounded in a consistent socioeconomic narrative (SSP storyline)
- Selected from IAM ensembles to span key uncertainties
- Provide boundary conditions for CMIP7 Earth system models

---

## The Seven Marker Scenarios

| Label | SSP | Pathway | IAM model | Peak warming |
|-------|-----|---------|-----------|-------------|
| <span class="scenario-vl">VL</span> | SSP1 | Very Low Emissions | REMIND-MAgPIE 3.5 | ~1.5°C |
| <span class="scenario-ln">LN</span> | SSP2 | Low Overshoot | AIM 3.0 | ~1.6°C (overshoot) |
| <span class="scenario-l">L</span>  | SSP2 | Low Emissions | MESSAGEix-GLOBIOM | ~2°C |
| <span class="scenario-ml">ML</span> | SSP2 | Medium-Low Emissions | COFFEE 1.6 | ~2.5°C |
| <span class="scenario-m">M</span>  | SSP2 | Medium Emissions | IMAGE 3.4 | ~3°C |
| <span class="scenario-h">H</span>  | SSP3 | High Emissions | GCAM 8s | ~4°C |
| <span class="scenario-hl">HL</span> | SSP5 | High → Low (CDR) | WITCH 6.0 | ~2.5°C |

<div class="small">

Colors used consistently throughout this presentation

</div>

---

## Scenario Narratives: SSP1 — Sustainability

<div class="columns">
<div>

**<span class="scenario-vl">VL — SSP1 "Very Low Emissions"</span>**
*Model: REMIND-MAgPIE 3.5-4.11*

- Strong global cooperation on sustainability
- Rapid decarbonisation of energy and land use
- High penetration of renewables by 2050
- Net-negative CO₂ by mid-century via BECCS/AFOLU
- Low population growth, high human development
- Methane and aerosol reductions track CO₂

**Warming target:** Below 1.5°C with high confidence

</div>
<div class="fig-placeholder">

[FIG: VL scenario CO₂ emissions and key drivers 2020–2100]
*(to be generated from scenariomip_default outputs)*

</div>
</div>

---

## Scenario Narratives: SSP2 — Middle of the Road

<div class="columns">
<div>

**<span class="scenario-l">L — SSP2 "Low Emissions"</span>**
*Model: MESSAGEix-GLOBIOM-GAINS 2.1-M-R12*

- Moderate ambition, consistent with 2°C
- Net-zero CO₂ around 2060–2070
- Significant CDR deployment post-2060

**<span class="scenario-ml">ML — SSP2 "Medium-Low"</span>**
*Model: COFFEE 1.6*

- Policies consistent with current NDC+ ambition
- Net-zero CO₂ around 2075
- Moderate CDR reliance

**<span class="scenario-m">M — SSP2 "Medium"</span>**
*Model: IMAGE 3.4*

- Limited additional policy beyond current trends
- CO₂ continues rising beyond 2050
- ~3°C by 2100

</div>
<div class="fig-placeholder">

[FIG: L, ML, M CO₂ emissions 2020–2100 on same axes]
*(to be generated)*

</div>
</div>

---

## Scenario Narratives: Overshoot and High Fossil

<div class="columns">
<div>

**<span class="scenario-ln">LN — SSP2 "Low Overshoot"</span>**
*Model: AIM 3.0*

- Temporary overshoot of 1.5°C before returning
- Deep negative emissions required post-2070
- High CDR deployment (BECCS, DACCS)
- Tests climate reversibility

**<span class="scenario-h">H — SSP3 "High Emissions"</span>**
*Model: GCAM 8s*

- Regional rivalry, limited cooperation
- High fossil fuel use, slow transition
- ~4°C by 2100; continued rise to 2500

**<span class="scenario-hl">HL — SSP5 "High then Low"</span>**
*Model: WITCH 6.0*

- Fossil-fuel development path to 2050
- Then aggressive CDR and clean energy switch
- High overshoot, high CDR — stress-tests reversibility

</div>
<div class="fig-placeholder">

[FIG: LN, H, HL CO₂ emissions — showing overshoot and high-CDR pathways]
*(to be generated)*

</div>
</div>

---

## CO₂ Emissions: All Seven Scenarios

<div class="fig-placeholder" style="min-height:380px;">

[FIG: Total CO₂e emissions 1950–2100, all 7 scenarios, coloured by label]
*(to be generated from scenariomip_default outputs — `fair_co2e_emissions_1750-2500.csv`)*

</div>

<div class="small">

Historical period (black), future projections coloured by scenario. Note the spread from net-negative (VL, LN) to continued high emissions (H).

</div>

---

## Temperature Outcomes to 2100

<div class="fig-placeholder" style="min-height:380px;">

[FIG: Temperature anomaly 1850–2100, all 7 scenarios, median + 5–95% ensemble range]
*(to be generated from `fair_temperature_1750-2500.csv`)*

</div>

<div class="small">

FaIR v2.2 probabilistic projections; shading shows 5th–95th percentile of 1000-member calibrated ensemble. Historical (black) blends to scenario colours at 2023.

</div>

---

## Non-CO₂ Forcing: CH₄ and Aerosols

<div class="columns">
<div class="fig-placeholder">

[FIG: CH₄ emissions 2000–2100, all scenarios]
*(to be generated from emissions_by_species data)*

</div>
<div class="fig-placeholder">

[FIG: Sulfur emissions 2000–2100, all scenarios]
*(to be generated)*

</div>
</div>

**Key points:**
- Methane mitigation is scenario-dependent: VL and L see aggressive reductions; H maintains high agricultural CH₄
- Sulfur (aerosol precursor) declines across all scenarios — aerosol unmasking effect
- Non-CO₂ forcing contributes significantly to near-term warming spread

---

## CDR in the Scenarios

<div class="columns">
<div>

**Carbon Dioxide Removal is central to ambition:**

- All mitigation scenarios rely on CDR to achieve net-zero or net-negative
- **Gross negative emissions** components in 2100:
  - BECCS (Bioenergy + CCS)
  - AFOLU (land sinks: reforestation, soil carbon)
  - DACCS (Direct Air Capture)
  - Enhanced weathering, ocean CDR, biochar

- **LN and HL** rely most heavily on CDR
- Technology mix differs across scenarios and IAMs

</div>
<div class="fig-placeholder">

[FIG: CDR breakdown by technology type for each scenario at 2100]
*(to be generated — stacked bar or area plot)*

</div>
</div>

---

<!-- _class: section-header -->

## Part III: Extensions Beyond 2100 — FLEX

---

## Why Extend Beyond 2100?

<div class="columns">
<div>

**IAM scenarios end at 2100 — but the climate system doesn't**

Key processes requiring multi-century forcing:
- **Ice sheet dynamics** — Greenland/Antarctic response on centennial timescales
- **Permafrost carbon** — slow release of soil carbon
- **Sea level rise commitment** — centuries-long thermal expansion
- **Ecosystem reorganisation** — biome shifts lag forcing

**CMIP7 ESMs need forcing to 2300–2500**

Without consistent extensions, each modelling centre makes independent ad-hoc choices → incomparable results

</div>
<div class="fig-placeholder">

[FIG: Schematic of slow climate processes and their characteristic timescales]
*(to be generated or adapted from literature)*

</div>
</div>

---

## FLEX: Framework for Long-term EXtensions

**Sanderson et al. (in prep.)** — open-source toolkit for scenario extensions

<div class="highlight">

FLEX allows scenarios to be indefinitely extended by defining a concise list of properties (e.g. net-zero timing, methane policy, carbon removal assumptions), using storylines to generate self-consistent, harmonised emissions trajectories.

</div>

<div class="columns">
<div>

**Key design principles:**
- Continuity with IAM scenario narratives
- Physical plausibility (no discontinuities)
- Internally consistent across species
- Configurable via simple YAML files
- Reproducible, open-source (Python)

</div>
<div>

**Pipeline:**
1. CO₂ fossil fuel storyline
2. AFOLU extension
3. CDR disaggregation
4. Non-CO₂ species (CH₄, Sulfur, …)
5. FaIR climate simulation

</div>
</div>

---

## CO₂ Storyline Types

Three parameterised functional forms describe post-2100 CO₂ fossil fuel evolution:

<div class="columns3">
<div>

**CS — Constant–Sigmoid**
Hold at 2100 value, then sigmoid ramp to zero
*Used for: M (medium)*

</div>
<div>

**ECS — Exponential–Constant–Sigmoid**
Exponential trend to a plateau, then sigmoid to zero (or negative)
*Used for: VL, LN, L, ML, H, HL*

</div>
<div>

**CSCS — Double Sigmoid**
Two-phase transition through intermediate value
*Used for: more complex reversals*

</div>
</div>

<div class="fig-placeholder">

[FIG: Three storyline types illustrated on same axes — CS, ECS, CSCS schematic]
*(to be generated — analytic curves)*

</div>

---

## Fossil CO₂ Extensions: All Scenarios

<div class="fig-placeholder" style="min-height:380px;">

[FIG: CO₂ FFI emissions 1750–2500, all 7 scenarios, showing pre-2100 IAM + post-2100 FLEX extension]
*(to be generated from `fair_emissions_by_species.csv` — CO2 FFI column)*

</div>

<div class="small">

Solid: IAM scenarios (1750–2100). Dashed extension: FLEX storylines (2100–2500). Vertical line at 2100 marks the handoff.

</div>

---

## AFOLU and CDR Extensions

<div class="columns">
<div class="fig-placeholder">

[FIG: CO₂ AFOLU emissions 1750–2500, all scenarios]
*(to be generated)*

</div>
<div class="fig-placeholder">

[FIG: Total CDR by scenario 2000–2500 — stacked by technology]
*(to be generated)*

</div>
</div>

**Extension strategies:**
- **NEG strategy** (VL, LN, L, ML, HL): gross positive emissions decay exponentially; CDR fills residual to match net target
- **POS strategy** (M, H): CDR held constant at 2100 level; gross positive tracks fossil storyline

---

## CDR Technology Disaggregation

<div class="columns">
<div>

**Six CDR categories tracked:**
1. **BECCS** — Bioenergy with carbon capture
2. **DACCS** — Direct air capture + storage
3. **Ocean CDR** — Alkalinity enhancement, iron fertilisation
4. **Enhanced Weathering** — Mineral silicate spreading
5. **Biochar** — Pyrolysis of biomass
6. **Soil Carbon Management** — Improved agricultural practices

Technology mix at 2100 is inherited from IAM scenarios, then held constant proportionally through the extension period.

</div>
<div class="fig-placeholder">

[FIG: CDR by technology 2000–2500, stacked area chart, for VL and HL scenarios]
*(to be generated)*

</div>
</div>

---

## Non-CO₂ Extensions: Methane

<div class="columns">
<div>

**CH₄ extension approach:**
- Sigmoid transition from 2100 IAM value to a specified 2500 target
- Targets set per-scenario to reflect narrative consistency:
  - VL: 95 Mt/yr (strong mitigation)
  - L, LN: 95–150 Mt/yr
  - ML: 120 Mt/yr
  - M: 450 Mt/yr (limited agriculture policy)
  - H: 520 Mt/yr (high agricultural emissions)
  - HL: 110 Mt/yr

</div>
<div class="fig-placeholder">

[FIG: CH₄ emissions 1750–2500, all scenarios, showing sigmoid transition post-2100]
*(to be generated from `fair_emissions_by_species.csv`)*

</div>
</div>

---

## Non-CO₂ Extensions: Aerosols (Sulfur)

<div class="columns">
<div>

**Sulfur extension:**
- Sulfur is an aerosol precursor — reduction causes near-term warming (aerosol unmasking)
- Post-2100 targets reflect energy system decarbonisation
  - VL: 20 Mt S/yr (residual industrial)
  - LN: 10 Mt S/yr (near-zero)
  - H: 50 Mt S/yr (continued fossil use)

**Other non-CO₂ species:**
- N₂O, halocarbons, NOₓ, BC, OC follow IAM trajectories or auto-calculated targets
- Regional composition maintained at 2100 ratios through extension

</div>
<div class="fig-placeholder">

[FIG: Sulfur emissions 1750–2500, all scenarios]
*(to be generated)*

</div>
</div>

---

## Climate Outcomes: Extended Temperature Projections

<div class="fig-placeholder" style="min-height:380px;">

[FIG: Temperature anomaly (relative to 1850–1900) 1750–2500, all 7 scenarios, median + 5–95% range]
*(to be generated from `fair_temperature_1750-2500.csv` — existing extensions.png plot)*

</div>

<div class="small">

Long-term stabilisation levels diverge markedly. VL stabilises below 1.5°C; H continues warming through 2500. HL peaks mid-century then declines due to CDR.

</div>

---

---

# Extending LUH3 Land‑Use Fields Beyond 2100

---

## The problem

IAMs give us gridded land-use states + rates to **2100**, but CMIP needs fields to **2500**.

We also have a global **AFOLU CO₂ trajectory** out to 2500:

![center w:820](figures/fig1_afolu_targets.png)

A naive linear ramp of rates to zero ignores carbon-cycle inertia — regrowing forests keep absorbing CO₂ long after planting. We need a smarter ramp.

---

## The carbon-cycle model

Four-predictor regression fit to pre-2100 IAM data:

$$\text{AFOLU}(t) = \beta + \gamma \cdot t + \alpha_{\text{trans}} \cdot F^{\text{trans}}(t) + \alpha_{\text{stock}} \cdot F^{\text{stock}}(t;\, \tau)$$

| Term | What it captures |
|------|-----------------|
| $\beta + \gamma \cdot t$ | Baseline + secular trend |
| $\alpha_{\text{trans}} \cdot F^{\text{trans}}$ | Instantaneous carbon from land-type conversion |
| $\alpha_{\text{stock}} \cdot F^{\text{stock}}$ | Cohort-based regrowth: $G_v(t) = G_v(t{-}1)\,e^{-1/\tau} + \Delta A_v(t)$ |

Stock-change creates **committed removals** from past reforestation that decay with timescale $\tau$. Profile-likelihood scan over $\tau$; OLS for the rest.

---

## Calibration fit

Four-predictor regression fit to pre-2100 IAM data:

$$\text{AFOLU}(t) = \beta + \gamma \cdot t + \alpha_{\text{trans}} \cdot F^{\text{trans}}(t) + \alpha_{\text{stock}} \cdot F^{\text{stock}}(t;\, \tau)$$
![center w:900](figures/fig2_calibration_fit.png)

---

## Calibration results

| | **VL** (Very Low) | **H** (High) |
|---|---|---|
| Model / IAM | REMIND-MAgPIE | GCAM 8s |
| State vars | 13 (full LUH set) | 9 (aggregated) |
| $\tau$ | 35 yr | 20 yr (fixed) |
| $R^2$ | 0.990 | 0.924 |
| Ramp → 0 at | 2143 | 2143 |
| Committed removal | −660 Mt CO₂/yr | +247 Mt CO₂/yr |

VL: strong fit, large committed sink from ongoing reforestation.
H: noisier (fewer categories), 3-predictor fallback ($\alpha_\text{stock}$ forced to 0).

---

## Forward solve → the AFOLU-consistent ramp

Invert the model to get $r(t)$:

$$r(t) = \frac{\text{AFOLU}_{\text{target}}(t) - \alpha_{\text{stock}} \cdot S_{\text{committed}}(t)}{\text{baseline} + \alpha_{\text{trans}} \cdot F^{\text{trans}}_{\text{unit}} + \alpha_{\text{stock}} \cdot S_{\text{new}}}$$

Each year feeds back into next year's cohort → sequential solve, clamped to $[0, 1]$.

![center w:820](figures/fig3_ramp.png)

Both reach zero by ~2143, but the *shapes* differ due to stock-change feedback.

---

## Verification: reconstructed vs target AFOLU

Does the ramp reproduce the IAM trajectory when plugged back in?

![center w:900](figures/fig4_extension_verify.png)

Gridded extension applies $r(t)$ cell-by-cell: $\;f_v(t{+}1) = f_v(t) + r(t) \cdot \dot{f}_v^{2100}$

Per-cell conservation enforced (fractions sum to 1, clamped ≥ 0, residual absorbs excess). Output: 0.25° NetCDF, ~1.4 GB total for both scenarios.

---

## Wood harvest + next steps

Wood harvest demand ramped linearly (country-level); for GLM3: $h(t) = \max(h_{\text{maint}},\, \text{file})$

![center w:900](figures/fig5_woodharvest.png)

**Done** ✓ VL + H complete, shared on Google Drive, pipeline automated (`src/pipeline.py`)
**Next** → 5 remaining scenarios (L, LN, M, ML, HL) as input data arrives

---

## Long-Term Forcing and Concentrations

<div class="columns">
<div class="fig-placeholder">

[FIG: Total radiative forcing 1750–2500, all scenarios, median + range]
*(to be generated from `fair_forcing_sum_1750-2500.csv`)*

</div>
<div class="fig-placeholder">

[FIG: CO₂ concentration 1750–2500, all scenarios]
*(to be generated from `fair_concentration_ghgs_1750-2500.csv`)*

</div>
</div>

---

## Temperature Probability Distributions

<div class="fig-placeholder" style="min-height:380px;">

[FIG: ECDF of temperature at 2100, 2300, and maximum — all scenarios]
*(existing plot: `temperature_ecdf.png` from scenariomip_default)*

</div>

<div class="small">

Each curve shows empirical CDF across 1000 FaIR ensemble members. Vertical spread reflects carbon cycle and climate sensitivity uncertainty propagated through the emissions-driven framework.

</div>

---

<!-- _class: section-header -->

## Part IV: Counterfactuals with FLEX

---

## Why Counterfactuals?

**Standard scenario exercises explore ad-hoc futures — but policy asks sharper questions:**

- *What would have happened without a specific policy?*
- *What temperature outcome is achievable if net-zero is delayed by 10 years?*
- *How does CDR deployment level affect peak warming?*

**Counterfactual scenarios** hold all else equal and vary a single dimension — enabling causal attribution of climate outcomes to policy choices.

<div class="highlight">

FLEX enables counterfactuals by optimising extension parameters to match a prescribed temperature target, starting from any existing scenario as a baseline.

</div>

---

## WIEMIP: Warming Impacts Experiment

**First application of FLEX counterfactuals**

<div class="columns">
<div>

**Design:**
- Take three marker scenarios (VL, ML, HL) as source
- Construct counterfactual (-CF) variants that hit prescribed warming targets using optimised CDR/net-zero timing
- Source and CF pairs share the same non-CO₂ emissions
- Difference in temperature outcome attributable to CO₂ policy

**Counterfactual targets:**
- HL-CF: Match lower warming of ML
- ML-CF: Match lower warming of L
- VL-CF: Match lower warming of net-zero

</div>
<div class="fig-placeholder">

[FIG: WIEMIP source/CF scenario pairs — CO₂ emissions and temperature outcomes]
*(existing: `cf_scenarios.png` from WIEMIP outputs)*

</div>
</div>

---

## FLEX Optimisation: How It Works

<div class="columns">
<div>

**Problem:** Find extension parameters such that the FaIR median temperature at a target year matches a prescribed value.

**Method:** `scipy.optimize.differential_evolution`
- Global optimisation — avoids local minima
- Parameters: CDR scaling, net-zero timing, fossil decay rate
- Objective: minimise |T(target_year) − T_target|
- Each evaluation: full FLEX extension + FaIR simulation

**Verification:** After optimisation, re-run FaIR with the full ensemble to confirm median matches target

</div>
<div class="fig-placeholder">

[FIG: Optimisation convergence plot for HL-CF target]
*(existing: `optimization_HL-CF_verification.png`)*

</div>
</div>

---

## Counterfactual Results: CO₂ Emissions

<div class="fig-placeholder" style="min-height:380px;">

[FIG: CO₂ total emissions (FFI + AFOLU) for source and CF scenario pairs, 1900–2300]
*(to be generated — cf_scenarios left panel)*

</div>

<div class="small">

Solid: source scenario. Dashed: counterfactual variant. Same non-CO₂ forcing; difference is CO₂ policy only.

</div>

---

## Counterfactual Results: Temperature

<div class="fig-placeholder" style="min-height:380px;">

[FIG: Median temperature + 5–95% range for each source/CF pair, 1900–2300; target temperatures shown as dashed horizontal lines]
*(to be generated — cf_scenarios right panel)*

</div>

<div class="small">

The optimised CF scenarios hit their prescribed warming targets at 2200. Uncertainty ranges illustrate the residual spread from carbon cycle and climate sensitivity.

</div>

---

## FLEX: Future Applications

<div class="columns">
<div>

**Already demonstrated:**
- ScenarioMIP-CMIP7 default extensions (7 scenarios, 1750–2500)
- WIEMIP counterfactuals (HL-CF, ML-CF, VL-CF)

**Planned uses:**
- **Space-spanning scenarios** — systematically fill the warming level × CDR deployment space
- **Delayed NDC scenarios** — sensitivity to net-zero timing
- **Non-CO₂ policy scenarios** — isolate methane mitigation contributions
- **ISIMIP forcing** — provide consistent long-period forcing for impact models
- **Custom ensembles** — any user-specified target via YAML config

</div>
<div class="fig-placeholder">

[FIG: Schematic of FLEX scenario space — warming target vs. CDR deployment, showing coverage by existing and planned scenarios]
*(to be generated)*

</div>
</div>

---

## FLEX Architecture

<div class="columns">
<div>

**Open-source Python toolkit:**

```
FLEX/
├── configs/          # YAML scenario configs
├── src/flex/
│   ├── config.py     # Config loader
│   ├── optimise.py   # Differential evolution
│   └── ...           # Extension functions
├── notebooks/
│   ├── 5191_extension.py
│   ├── 5195_optimise.py
│   ├── 5196_apply_optimised.py
│   ├── 5201_fair_simulations.py
│   └── 5202_fair_plots.py
└── scripts/
    └── run_pipeline.py
```

</div>
<div>

**Key features:**
- Papermill pipeline with `--from` resume support
- Parallel optimisation (`--parallel N`)
- FaIR v2.2 probabilistic ensemble (1000 members)
- All outputs in IAMC-compatible CSV format
- Jupytext for version-controlled notebooks
- Pixi for reproducible environments

**To run ScenarioMIP default:**
```bash
pixi run pipeline scenariomip_default
```

</div>
</div>

---

## Summary: ScenarioMIP-CMIP7

<div class="columns">
<div>

**Seven marker scenarios** spanning aggressive mitigation to high-emissions futures

**Emissions-driven** protocol in CMIP7 enables correct propagation of carbon cycle feedbacks

**flat10MIP** provides a dedicated experiment to characterise TCRE and reversibility

**Extensions to 2500** via FLEX ensure consistent long-term boundary conditions for ice-sheet, permafrost, and sea-level models

</div>
<div>

**FLEX counterfactuals** (WIEMIP) demonstrate causal attribution of temperature outcomes to CO₂ policy

**Future development:**
- Space-spanning scenario library
- Integration with ISIMIP and regional downscaling
- Target-seeking optimisation for arbitrary warming levels

**All data and code open-source** — FLEX available on GitHub

</div>
</div>

---

## Key References

<div class="small">

- **Van Vuuren et al. (2026)** — The Scenario Model Intercomparison Project for CMIP7 (ScenarioMIP-CMIP7). *GMD* 19, 2627. https://doi.org/10.5194/gmd-19-2627-2026

- **Sanderson et al. (2024)** — The need for carbon-emissions-driven climate projections in CMIP7. *GMD* 17, 8141. https://doi.org/10.5194/gmd-17-8141-2024

- **Sanderson et al. (2025)** — flat10MIP: an emissions-driven experiment to diagnose the climate response to positive, zero and negative CO₂ emissions. *GMD* 18, 5699. https://doi.org/10.5194/gmd-18-5699-2025

- **Dunne et al. (2025)** — An evolving Coupled Model Intercomparison Project phase 7 (CMIP7) and Fast Track in support of future climate assessment. *GMD* 18, 6671. https://doi.org/10.5194/gmd-18-6671-2025

- **Sanderson et al. (in prep.)** — FLEX: Framework for Long-term EXtensions. *GMD* (submitted).

- **Smith et al. (2021)** — FaIR v2.0: a generalised impulse response model for climate uncertainty and future scenario exploration. *GMD*.

</div>

---

<!-- _paginate: false -->

## Questions?

<br>

**Benjamin Sanderson**
CICERO Center for International Climate Research, Oslo
benjamin.sanderson@cicero.oslo.no

<br>

**FLEX codebase:** `github.com/benmsanderson/FLEX` *(link TBC)*

**ScenarioMIP data:** ESGF / CMIP7 data nodes

---

<!-- _paginate: false -->

## Appendix: Scenario Parameters

| Scenario | Fossil type | CDR strategy | CH₄ 2500 target | Sulfur 2500 target |
|----------|------------|-------------|----------------|-------------------|
| VL | ECS (→ −3500 Mt) | NEG (τ=100, offset=60) | 95 Mt/yr | 20 Mt S/yr |
| LN | ECS (→ −24000 Mt) | NEG (τ=50, offset=100) | 150 Mt/yr | 10 Mt S/yr |
| L  | ECS (linear) | NEG (τ=50, offset=50) | 95 Mt/yr | auto |
| ML | ECS (→ −13000 Mt) | NEG (τ=100, offset=0) | 120 Mt/yr | 20 Mt S/yr |
| M  | CS | POS | 450 Mt/yr | 20 Mt S/yr |
| H  | ECS (linear) | POS | 520 Mt/yr | 50 Mt S/yr |
| HL | ECS (→ −22000 Mt) | NEG (τ=80, offset=20) | 110 Mt/yr | 10 Mt S/yr |

---

<!-- _paginate: false -->

## Appendix: FaIR Ensemble Setup

<div class="columns">
<div>

**FaIR v2.2 configuration:**
- 1000-member probabilistic ensemble
- Calibrated to IPCC AR6 assessed ranges
- Emissions-driven: CO₂, CH₄, N₂O, halocarbons, aerosols, ozone
- Run 1750–2500 for all scenarios

**Key outputs:**
- Temperature (median, 5th, 95th percentile)
- Radiative forcing by species
- CO₂/CH₄ concentrations
- ECDF data for impact assessment

</div>
<div class="fig-placeholder">

[FIG: FaIR calibration — temperature vs. IPCC assessed ranges]
*(from FaIR documentation or to be generated)*

</div>
</div>

---

<!-- _paginate: false -->

## Appendix: FLEX Extension Timeline

<div class="fig-placeholder" style="min-height: 380px;">

[FIG: 8-panel extensions diagnostic (extensions.png) for scenariomip_default]
*(existing plot from 5202_extension_fair_plots output)*

</div>
