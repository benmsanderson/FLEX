---
marp: true
theme: newton
paginate: true
#backgroundColor: white
style: |
  section {
    font-size: 21px;
    padding: 38px 52px 38px 52px;
    color: #222;
  }
  h1 { font-size: 38px; color: #1a2e5a; margin-bottom: 10px; }
  h2 { font-size: 28px; color: #1a2e5a; border-bottom: 2px solid #c8d4ee; padding-bottom: 5px; margin-bottom: 16px; }
  h3 { font-size: 22px; color: #2c4a7a; margin-bottom: 8px; }
  section.title h1 { font-size: 42px; border: none; }
  section.title h2 { border: none; color: #3a5a8a; font-size: 24px; font-weight: normal; }
  section.divider { background: #1a2e5a; color: white; display: flex; flex-direction: column; justify-content: center; }
  section.divider h1 { color: white; font-size: 44px; border: none; }
  section.divider h2 { color: #aac4ee; border: none; font-weight: normal; }
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
  .columns-wf { display: grid; grid-template-columns: 2fr 3fr; gap: 28px; }
  .columns-swf { display: grid; grid-template-columns: 2fr 4fr; gap: 28px; }  
  .columns3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 18px; }
  .col { }
  .highlight {
    background: #eef2ff;
    border-left: 4px solid #3a5a8a;
    padding: 10px 16px;
    border-radius: 0 6px 6px 0;
    margin: 10px 0;
    font-size: 19px;
  }
  .highlight-warm {
    background: #fff8ee;
    border-left: 4px solid #e07020;
    padding: 10px 16px;
    border-radius: 0 6px 6px 0;
    margin: 10px 0;
  }
  .fig {
    background: #f0f4ff;
    border: 2px dashed #8899cc;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    color: #445577;
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 160px;
  }
  .fig-tall { min-height: 340px; }
  .fig-short { min-height: 100px; }
  .small { font-size: 16px; color: #556; }
  .vsmall { font-size: 14px; color: #778; }
  .scen-vl  { color: #16188F; font-weight: bold; }
  .scen-ln  { color: #0097a0; font-weight: bold; }
  .scen-l   { color: #208050; font-weight: bold; }
  .scen-ml  { color: #907000; font-weight: bold; }
  .scen-m   { color: #e06000; font-weight: bold; }
  .scen-h   { color: #a41212; font-weight: bold; }
  .scen-hl  { color: #8a10a8; font-weight: bold; }
  .scen-com { color: #555555; font-weight: bold; }
  table { font-size: 17px; width: 100%; border-collapse: collapse; }
  th { background: #1a2e5a; color: white; padding: 6px 10px; }
  td { padding: 5px 10px; border-bottom: 1px solid #dde; }
  tr:nth-child(even) td { background: #f4f6fb; }
  footer { font-size: 13px; color: #999; }
  img { max-width: 100%; max-height: 420px; object-fit: contain; display: block; margin: 0 auto; }
  .fig img { max-height: 380px; }
  .pipeline { display: flex; align-items: center; justify-content: center; gap: 0; margin-top: 18px; font-size: 14px; flex-wrap: nowrap; overflow-x: auto; }
  .pipeline-box { border-radius: 8px; padding: 8px 12px; text-align: center; min-width: 100px; border: 2px solid; display: inline-flex; flex-direction: column; align-items: center; justify-content: center; }
  .pipeline-arrow { font-size: 48px; padding: 0 4px; min-width: 20px; background: transparent !important; color: black !important; }
  section .arrow-config { color: #3a5a8a !important; }
  section .arrow-stage { color: #667 !important; }
  section .arrow-output { color: #e07020 !important; }
  section .arrow-final { color: #2e7d32 !important; }
  .pipeline-config { background: #eef2ff; border-color: #3a5a8a; color: #3a5a8a; }
  .pipeline-stage { background: #f8f9ff; border-color: #667; color: #222; border-width: 1.5px; min-width: 90px; }
  .pipeline-output { background: #fff8ee; border-color: #e07020; color: #222; }
  .pipeline-final { background: #e8f5e9; border-color: #2e7d32; color: #222; }
---

<!-- _class: title -->
<!-- _paginate: false -->

# Introducing FLEX: a simplified framework for future scenario exploration

Shivika Mittal<sup>1</sup>, Benjamin Sanderson<sup>1</sup>, **Marit Sandstad**<sup>1</sup>, Jarmo Kikstra<sup>2</sup>, Zebedee Nicholls<sup>2,3,4</sup> and Marko Zecchetto<sup>2</sup>
<sup>1</sup>CICERO Center for International Climate Research, Oslo, Norway
<sup>2</sup>International Institute for Applied Systems Analysis , Vienna, Austria
<sup>3</sup>Climate Resource, Berlin, Germany
<sup>4</sup>School of Geography, Earth and Atmospheric Sciences, The University of Melbourne, Melbourne, Victoria, Australia



**Climate Risk Storylines and Scenarios: From physical modelling to co-production for decision-making**

*EGU 2026, Monday May 4th* 

---

## Why FLEX? The case for idealised scenario extension

IAMs provide forcing to 2100 or shorter — but many Earth system processes respond on centennial or longer timescales.

Exploration of counterfactuals scenarios or scenarios that reach specific temperature targets are important

<div class="columns">
<div>

**Processes requiring long forcing:**

| Process | Characteristic timescale |
|---------|:----------------------:|
| Greenland ice sheet | Centuries–millennia |
| Antarctic ice sheet | Centuries–millennia |
| Sea level rise commitment | Centuries |
| Permafrost carbon release | Decades–centuries |
| Deep ocean heat uptake | Decades–centuries |
| Biome reorganisation | Decades–centuries |



</div>
<div class="highlight">

**Extensions:** Expand existing scenario beyond the economic modelling to **2300** or **2500*

**Counterfactual:** Overshoot versus hold at peak temperature

**Fill the physical trajectory space** Fast turn-over idealised scenarios

</div>
</div>

---

## FLEX: Framework for Long-term EXtensions

**Sanderson et al. (in preparation)** — Extends ScenarioMIP emissions beyond 2100 to 2500.

<div class="columns">
<div>

**Design principles:**
- No discontinuities at point of extension, differentiable if possible 
- Physically plausible, internally consistent across species
- Configurable via YAML; reproducible, open-source

</div>
</div>

<div class="pipeline">
<div class="pipeline-box pipeline-config">
<b>YAML config</b><br/><i style="font-size:12px;">scenarios, targets</i></div>
<div class="pipeline-arrow arrow-config">▸</div>
<div class="pipeline-box pipeline-stage">
  Non-CO₂<br/>species</div>
<div class="pipeline-arrow arrow-stage">▸</div>
<div class="pipeline-box pipeline-stage">
  AFOLU<br/>extension</div>
<div class="pipeline-arrow arrow-stage">▸</div>
<div class="pipeline-box pipeline-stage">
  CO₂ fossil<br/>storyline</div>
<div class="pipeline-arrow arrow-stage">▸</div>
<div class="pipeline-box pipeline-output">
<b>FaIR v2.2</b><br/><i style="font-size:12px;">841-member ens.</i></div>
<div class="pipeline-arrow arrow-final">▸</div>
<div class="pipeline-box pipeline-final">
<b>Temperature</b><br/>Forcing · Conc.</div>
</div>

---

## Non-CO₂ Extensions: Smooth transit to global minima

<div class="columns">
<div>

**ML - C6F14**

<div class="fig">

![center w:900](../outputs/presentation/non_co2/extended_match_totals_SSP5-Medium-LowEmissions_a_WITCH6.0_C6F14.png)

</div>

</div>

<div>

**ML - N2O**

<div class="fig">

![center w:900](../outputs/presentation/non_co2/extended_match_totals_SSP5-Medium-LowEmissions_a_WITCH6.0_N2O.png)

</div>
</div>

---

## Non-CO₂ Extensions: CH₄ and Sulfur

<div class="columns-wf">
<div>

**Methane and Sulfur transition to 2500 target:**

Targets set to reflect each scenario's long-term narrative:

| Scenario | 2500 CH₄ target | 2500 SO₂ target |
|----------|:-----------:|:----------:|
| <span class="scen-vl">VL</span>, <span class="scen-l">L</span> | 95 Mt/yr | 20 Mt S/yr |
| <span class="scen-ln">LN</span> | 150 Mt/yr | 10 Mt S/yr |
| <span class="scen-ml">ML</span> | 120 Mt/yr | 20 Mt S/yr |
| <span class="scen-m">M</span> | 450 Mt/yr | 20 Mt S/yr |
| <span class="scen-h">H</span> | 520 Mt/yr | 50 Mt S/yr |
| <span class="scen-hl">HL</span> | 110 Mt/yr | 10 Mt S/yr |

</div>
<div class="fig">

![center w:900](../outputs/presentation/F11_ch4_1750_2500.png)

</div>
</div>

---

## CO₂ Fossil Fuel Storylines

Three functional forms parameterise the post-2100 fossil CO₂ trajectory, continuing each scenario's narrative:

<div class="columns3">
<div>

**CS — Constant–Sigmoid**
Hold at 2100 value, then sigmoid ramp to zero

*<span class="scen-m">M</span>: limited new policy*

</div>
<div>

**ECS — Exponential–Constant–Sigmoid**
Exponential trend to plateau, then sigmoid to zero or net-negative

*<span class="scen-vl">VL</span> <span class="scen-ln">LN</span> <span class="scen-l">L</span> <span class="scen-ml">ML</span> <span class="scen-h">H</span> <span class="scen-hl">HL</span>*

</div>
<div>

**CSCS — Double Sigmoid**
Two-phase transition for complex reversals

*Available for custom scenarios*

</div>
</div>

<div class="fig">

![center w:950](../outputs/presentation/F09_storyline_types_fossil.png)

</div>

---

## CDR Technology Disaggregation

<div class="columns-wf">
<div>

**Six CDR categories tracked through 2500:**

| Technology | Notes |
|------------|-------|
| BECCS | Bioenergy + CCS; land-use linked |
| DACCS | Direct Air Capture + storage |
| Ocean CDR | Alkalinity enhancement, fertilisation |
| Enhanced Weathering | Mineral silicate spreading |
| Biochar | Pyrolysis of biomass |
| Soil Carbon | Agricultural practice improvement |

Technology mix at 2100 inherited from the IAM and held proportionally constant. Total CDR scales with the net CO₂ storyline target. This same mix scaling is retained in regions and sectors also for non-CO2 species.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F10_cdr_aggregate.png)Preliminary ScenarioMIP results, not for redistribution




</div>


</div>

---
## Long-Term Climate Outcomes: 1750–2500

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F13_temperature_2500.png)

</div>

<div class="small">

VL stabilises below 1.5°C; H continues warming through 2500. HL peaks mid-21st century then declines with CDR — but recovery is slower than the warming, consistent with flat10MIP results.

</div>

---

## FLEX for WIEMIP: Counterfactual Scenario Pairs

Standard scenario exercises cannot answer **causal** questions about individual policy levers.

<div class="highlight">

*"How much additional sea level rise is committed by an overshoot trajectory, compared to maintaining the same peak warming level?"*

</div>

A core AR7-WG1-CH9 question. Answering it requires two scenarios **identical in all respects except CO₂ pathway**. FLEX enables this by **optimising extension parameters to hit a prescribed temperature target**, holding all non-CO₂ forcing fixed.

| Source | Counterfactual | Target | Key question |
|--------|---------------|--------|-------------|
| <span class="scen-hl">HL</span> (overshoot) | <span class="scen-hl">HL-CF</span> | Maintain peak warming | Cost of overshoot |
| <span class="scen-ml">ML</span> | <span class="scen-ml">ML-CF</span> | Match L-ambition warming | Benefit of deeper mitigation |
| <span class="scen-vl">VL</span> | <span class="scen-vl">VL-CF</span> | Residual at low end | Sensitivity at low forcing |

In each pair: non-CO₂ emissions are identical; CF adjusts CO₂ via optimised FLEX parameters. Any temperature difference is attributable **solely to CO₂ pathway**.

**Primary pair for AR7-CH9:** HL vs. HL-CF — overshoot vs. maintain-peak.

---

## Optimisation: Finding the Target-Consistent Pathway

<div class="columns-wf">
<div>

**Problem:** Find FLEX parameters such that **FaIR median temperature at a target year** matches a prescribed value.

**Method:** `differential_evolution` — global stochastic optimiser
- Decision variables: CDR scaling, net-zero timing, fossil decay rate
- ~200–500 evaluations, each running FLEX + FaIR 841-member ensemble
- Full ensemble re-run after convergence to verify and characterise uncertainty

</div>
<div class="fig">

![center w:900](../outputs/WIEMIP/optimization_HL-CF_verification.png)

</div>
</div>

---

## FLEX for WIEMIP Results: CO₂ Emissions and Temperature Trajectories


<div class="columns">
<div>

**Emissions**

<div class="fig">

![center w:900](../outputs/presentation/F15_wiemip_co2_emissions.png)

</div>

</div>

<div>

**Temperature outcomes**

<div class="fig">

![center w:900](../outputs/presentation/F16_wiemip_temperature.png)

</div>
</div>


<div class="small">

The CF pathway deploys CDR earlier and more deeply to suppress the overshoot. Non-CO₂ forcing is identical between source and CF — any difference in climate response is attributable to this CO₂ pathway difference alone.

</div>

---

## WIEMIP: HL Attribution

<div class="columns-wf">
<div>

**HL / HL-CF pair — clean experimental design for WG1-CH9:**

ESMs forced with both can attribute differences in:
- **Sea level commitment** — thermal expansion + ice sheets
- **Permafrost carbon release** — additional thaw under overshoot
- **Ocean heat content** — additional heat stored under higher peak

Non-CO₂ forcing is identical — any difference is attributable solely to the overshoot vs. maintain-peak choice.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F17_hl_attribution.png)

</div>
</div>

---


## Summary:

<div class="columns">
<div>

**FLEX extensions (1750–2500):**
- Consistent CO₂, AFOLU (LUH3-compatible), CDR, and non-CO₂ forcing beyond 2100
- Carbon-cycle-consistent AFOLU ramp avoids flux errors from naive rate ramps

</div>
<div>

**FLEX counterfactuals:**
- Designed for WG1-CH9: overshoot vs. maintain-peak-warming
- Clean experimental design — non-CO₂ forcing follow original; temperature difference attributable solely to CO₂ pathway
- Framework extensible to any temperature target or scenario pairing
- Could be used to extend a scenario beyond its peak

</div>
</div>

---

## Key References

<div class="small">

- **Meinshausen et al. (2024)** — A perspective on the next generation of Earth system model scenarios: towards representative emission pathways (REPs). *GMD* 17, 4533. https://doi.org/10.5194/gmd-17-4533-2024

- **Van Vuuren et al. (2026)** — The Scenario Model Intercomparison Project for CMIP7. *GMD* 19, 2627. https://doi.org/10.5194/gmd-19-2627-2026

- **Sanderson et al. (2024)** — The need for carbon-emissions-driven climate projections in CMIP7. *GMD* 17, 8141. https://doi.org/10.5194/gmd-17-8141-2024

- **Sanderson et al. (2025)** — flat10MIP: an emissions-driven experiment to diagnose the climate response to positive, zero and negative CO₂ emissions. *GMD* 18, 5699. https://doi.org/10.5194/gmd-18-5699-2025

- **Dunne et al. (2025)** — An evolving CMIP7 and Fast Track in support of future climate assessment. *GMD* 18, 6671. https://doi.org/10.5194/gmd-18-6671-2025

- **Lu et al. (2025)** — Earth system responses under a global 2°C-target scenario aligned with carbon neutrality pledges. *ERL* 20, 104049. https://doi.org/10.1088/1748-9326/adfbfb

- **Sanderson et al. (in prep.)** — FLEX: Framework for Long-term EXtensions. *GMD* (in preparation).

- **Smith et al. (2021)** — FaIR v2.0: a generalised impulse response model for climate uncertainty and future scenario exploration. *GMD*. https://doi.org/10.5194/gmd-14-3007-2021

- **Hurtt et al. (2020)** — Harmonization of global land use change and management for the period 850–2100 (LUH2). *GMD*. https://doi.org/10.5194/gmd-13-5425-2020

</div>

---

<!-- _paginate: false -->
<!-- _class: title -->

# Thank you

Shivika Mittal, Benjamin Sanderson, **Marit Sandstad**, Jarmo Kikstra, Zebedee Nicholls and Marco Zecchetto

marit.sandstad@cicero.oslo.no

*FLEX codebase: github.com/benmsanderson/FLEX (link TBC)*

---

<!-- _paginate: false -->

---

## Appendix A1: The Seven Marker Scenarios

<br>

| &nbsp; | SSP | Pathway | IAM model | ~2100 warming |
|--------|-----|---------|-----------|:---:|
| <span class="scen-vl">VL</span> | SSP1 | Very Low Emissions | REMIND-MAgPIE 3.5-4.11 | ~1.5°C |
| <span class="scen-ln">LN</span> | SSP2 | Low Overshoot | AIM 3.0 | ~1.6°C (peak ~1.8°C) |
| <span class="scen-l">L</span>   | SSP2 | Low Emissions | MESSAGEix-GLOBIOM-GAINS 2.1 | ~2°C |
| <span class="scen-ml">ML</span> | SSP2 | Medium-Low Emissions | COFFEE 1.6 | ~2.5°C |
| <span class="scen-m">M</span>  | SSP2 | Medium Emissions | IMAGE 3.4 | ~3°C |
| <span class="scen-h">H</span>  | SSP3 | High Emissions | GCAM 8s | ~4°C |
| <span class="scen-hl">HL</span> | SSP5 | Very High → CDR | WITCH 6.0 | ~2.5°C |

<div class="small">

Colours used consistently throughout this presentation. Warming levels are approximate FaIR medians relative to 1850–1900.

</div>

---

## Appendix A2: FLEX Extension Parameters

| Scenario | Fossil type | CO₂ target | CDR strategy | CH₄ 2500 | SO₂ 2500 |
|----------|------------|------------|-------------|:--------:|:--------:|
| <span class="scen-vl">VL</span> | ECS | −3,500 Mt | NEG τ=100, off=60 | 95 Mt/yr | 20 Mt S/yr |
| <span class="scen-ln">LN</span> | ECS | −24,000 Mt | NEG τ=50, off=100 | 150 | 10 |
| <span class="scen-l">L</span>   | ECS | linear→0 | NEG τ=50, off=50 | 95 | auto |
| <span class="scen-ml">ML</span> | ECS | −13,000 Mt | NEG τ=100, off=0 | 120 | 20 |
| <span class="scen-m">M</span>  | CS  | →0 | POS (CDR constant) | 450 | 20 |
| <span class="scen-h">H</span>  | ECS | linear→0 | POS (CDR constant) | 520 | 50 |
| <span class="scen-hl">HL</span> | ECS | −22,000 Mt | NEG τ=80, off=20 | 110 | 10 |

<div class="vsmall">NEG = gross-positive decays exponentially (timescale τ years, offset Mt/yr CDR floor); CDR fills residual. POS = CDR held constant at 2100 level; fossil follows storyline.</div>

---

<!-- _paginate: false -->

## Appendix A3: FaIR v2.2 Configuration

<div class="columns">
<div>

**Ensemble setup:**
- 1000-member probabilistic ensemble
- Parameters calibrated to IPCC AR6 assessed ranges (ECS, TCR, TCRE)
- Emissions-driven: CO₂, CH₄, N₂O, halocarbons, SO₂, BC, OC, ozone precursors
- Run period: 1750–2500 for all scenarios
</div>

<div>

**Key outputs:**
- Temperature (median, 5th, 95th percentile)
- Total and species-resolved radiative forcing
- CO₂, CH₄, N₂O concentrations
- CO₂-equivalent emissions (AR6 GWP100)
- ECDF data for probabilistic impact assessment
</div>

---

<!-- _paginate: false -->

## Appendix A4: Extensions 8-Panel Diagnostic

<div class="fig fig-tall">

![center w:900](../plots/scenariomip_default/extensions.png)

[FIG: 8-panel extensions diagnostic for scenariomip_default — CO₂ FFI, CO₂ AFOLU, CH₄, cumulative CO₂, Sulfur, total CO₂e, total forcing, temperature anomaly — all 1750–2500, all 7 scenarios]
</div>

---

## Appendix A5: CDR and Storage Limits

<div class="small">
<div class="fig">

![w:1000](../outputs/presentation/cdr_split.png)

</div>
*(Van Vuuren et al. 2026, Fig. 3, ML, HL & H rows)* — Annual and cumulative gross CO₂ fluxes for ML, H and HL markers through 2500. Right panels show cumulative removals against sequestered storage capacity limits (dashed red) and probable fossil reserves (brown).

</div>

---

## Appendix A6: AFOLU Beyond 2100: The Carbon-Cycle Inertia Problem

<div class="columns">
<div>

IAMs provide an **AFOLU CO₂ target trajectory** to 2500 — but converting this to consistent **gridded land-use fields** for LUH3 is non-trivial.

**The naïve approach fails:** simply ramping land-use change rates to zero ignores carbon-cycle inertia.
</div>
<div>

**Why inertia matters:**
- Forests reforested before 2100 continue absorbing CO₂ for decades after planting — **committed removals**
- A naive rate ramp overestimates net AFOLU flux early in the extension period and underestimates it later
- The discrepancy can exceed 200 MtCO₂/yr — material for the global carbon budget and incompatible with FLEX's CO₂ targets

</div>
</div>

---

## LUH3 Extension: A Carbon-Consistent Ramp

A carbon cycle model is calibrated to pre-2100 IAM data, then **inverted** to find the land-use change rate $r(t)$ that reproduces the AFOLU target post-2100.

<div class="columns-wf">
<div>

**Three flux channels in the model:**

| Channel | What it captures |
|---------|----------------|
| Transition flux | Instantaneous carbon from land-type conversion |
| Stock-change flux | Committed removals from forest cohorts, decaying with timescale ~35 years |
| Secular trend | Expanding reforestation area over time |



</div>
<div>

Once $r(t)$ is solved, it is applied cell-by-cell to the gridded LUH3 state fractions, with per-cell conservation enforced. BECCS biofuel area is scaled independently from the IAM's bioenergy trajectory.

</div>
</div>

---