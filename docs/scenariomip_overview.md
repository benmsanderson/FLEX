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
---

<!-- _class: title -->
<!-- _paginate: false -->

# Overview of Global Scenarios and ScenarioMIP CMIP7

**Benjamin Sanderson**
CICERO Center for International Climate Research, Oslo

*Prepared for WG1 AR7 authors*

---

## Outline

<div class="columns">
<div>

**1. Why scenarios?**
— role in climate science, history, Paris framing

**2. CMIP7 and emissions-driven projections**
— Fast Track, the case for emissions-driven, flat10MIP

**3. ScenarioMIP-CMIP7**
— the 7 marker scenarios, narratives, SSP2-com comparison, global outputs

</div>
<div>

**4. Extensions beyond 2100: FLEX**
— CO₂ storylines, CDR, AFOLU/LUH3, non-CO₂, long-term climate outcomes

**5. FLEX counterfactuals: WIEMIP**
— overshoot vs. maintain-peak-warming; optimisation for target temperatures

**6. Summary and outlook**

</div>
</div>

---

## The Role of Scenarios in Climate Science

Scenarios translate **human choices** into **physical climate forcing** — the bridge between policy and Earth system response.

<div class="columns-swf">
<div>

**What a scenario must do:**
- Convert socioeconomic assumptions into consistent emissions trajectories
- Force ESMs to produce comparable, multi-model projections
- Span the range of plausible futures — from aggressive action to limited ambition

**What AR7 needs:**
- Coverage of the post-Paris warming range (1.5–4°C)
- Long-term forcing for slow processes (ice sheets, permafrost, sea level)
- Consistency across gases, sectors, and spatial scales

</div>
<div class="fig">

![center w:1200](external_figures/meinshausen2024_f02_reps.png)

</div>
</div>

<div class="small">

*(Meinshausen et al. 2024, Fig. 2)* — Representative Emission Pathways: the scenario space CMIP7 must cover, from immediate action (IA2015) to fossil-fuel-intensive worlds (TEWA).

</div>

---

## A Brief History of Scenario Frameworks

| Generation | Scenario set | Primary metric | CMIP phase | Key advance |
|------------|-------------|----------------|------------|-------------|
| 1990s | SRES | Emissions | CMIP3 | Structured narratives |
| 2010s | RCPs | Radiative forcing | CMIP5 | Forcing-level design; model parallelism |
| 2010s | SSPs + RCPs | Emissions + forcing | CMIP6 | Shared socioeconomic pathways; scenario matrix |
| 2025+ | CMIP7 | **Emissions** | **CMIP7** | Emissions-driven as primary protocol |

**The CMIP7 shift:** moving from concentration- or forcing-driven to **emissions-driven** as the standard — placing carbon cycle feedbacks inside the simulation rather than outside it.

<div class="highlight">

Each generation has expanded coverage of the relevant uncertainty space while tightening consistency requirements across modelling groups.

</div>

---

## What the Paris Agreement Asks of Scenarios

The Paris Agreement targets (well below 2°C, pursuing 1.5°C) require scenarios that:

<div class="columns">
<div>

**Span the relevant space:**
- Deep mitigation consistent with 1.5°C (VL, LN)
- Current-policy trajectories (ML, M)
- High-end futures for impact research (H, HL)
- Overshoot and CDR-reliant pathways (LN, HL)

**Expose key uncertainties:**
- Net-zero timing and technology mix
- CDR deployment scale and permanence
- Non-CO₂ mitigation (CH₄, aerosols)
- Carbon cycle feedbacks under net-negative emissions

</div>
<div>

**Limitations of IAM-only ensembles:**
- Ad-hoc sampling of the future space — scenarios cluster around common thresholds
- Hard to isolate effects of individual policy levers
- No systematic coverage of intermediate warming levels

→ This motivates **FLEX**: a toolkit to extend and augment the standard scenario set

</div>
</div>

---

## CMIP7 and the Fast Track

**Dunne et al. (2025)** — *An evolving CMIP7 and Fast Track in support of future climate assessment*

<div class="columns-wf">
<div>

**CMIP7 objectives:**
- Inform IPCC AR7 (target: 2029)
- Prioritise policy-relevant experiments
- Reduce participation barriers for the Global South
- Improve data standards and reproducibility

**Fast Track:**
- A targeted subset of high-priority experiments designed to be available for AR7
- Includes DECK (piControl, abrupt-4xCO₂, 1pctCO₂, amip) plus **ScenarioMIP**
- Modelling groups commit to Fast Track first; broader MIPs follow

</div>
<div class="fig">

![center w:900](external_figures/dunne2025_f02_cmip7_fast_track.png)
*(Dunne et al. 2025, Fig. 2)*

</div>
</div>

---

## The Case for Emissions-Driven Simulations

**Sanderson et al. (2024)** — *The need for carbon-emissions-driven climate projections in CMIP7*, GMD 17, 8141

<div class="columns-wf">
<div>

**The problem with concentration-driven:**
- CO₂ pathway is fixed — carbon cycle cannot diverge
- Different models have different compatible emissions for the same concentrations → cross-model comparisons conflate forcing and feedback
- Misrepresents the policy question: **we control emissions, not concentrations**

**What emissions-driven adds:**
- Carbon cycle feedbacks propagate correctly into temperature uncertainty
- Fair cross-model comparison: same emissions, different outcomes
- Direct link to carbon budget frameworks

</div>
<div class="fig">

![center w:900](external_figures/sanderson2024_f01_uncertainty_propagation.png)
*(Sanderson et al. 2024, Fig. 1)*

</div>
</div>

---

## flat10MIP: Diagnosing Carbon Cycle Response

**Sanderson et al. (2025)** — *flat10MIP: an emissions-driven experiment …*, GMD 18, 5699

<div class="columns-wf">
<div>

**Motivation:**
- The proportionality between temperature and cumulative CO₂ (TCRE) is the foundation of carbon budgeting
- But is TCRE symmetric under negative emissions? Do models agree?
- Crucial for interpreting overshoot scenarios (LN, HL) in ScenarioMIP

**Experiment design:**
- Prescribed global CO₂ emissions: sustained flat +10 Gt CO₂/yr for 50 years, then linear ramp to zero, then negative
- All ESMs forced identically — isolates model differences in TCRE and reversibility
- Part of CMIP7 Fast Track

</div>
<div class="fig">

![center w:900](external_figures/sanderson2025_f01_flat10mip_design.png)
*(Sanderson et al. 2025, Fig. 1)*

</div>
</div>


---

## ScenarioMIP-CMIP7: Design Objectives

**Van Vuuren et al. (2026)** — Seven marker scenarios spanning aggressive mitigation to high emissions, grounded in SSP storylines. Primary protocol: **emissions-driven** with FLEX extensions to 2500.

![center w:1000](external_figures/vanvuuren2026_f01_scenariomip_design.png)

<div class="small">

*(Van Vuuren et al. 2026, Fig. 1)* — GHG emissions and temperature outcomes for the seven CMIP7 ScenarioMIP markers.

</div>

---

## The Seven Marker Scenarios

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

## Narrative: SSP1-VL — Sustainability

<div class="columns-swf">
<div>

**<span class="scen-vl">SSP1-VL "Very Low Emissions"</span>**
*REMIND-MAgPIE 3.5-4.11*

Strong global cooperation, rapid sustainability transition. Net-zero CO₂ by ~2060; net-negative thereafter. Strong AFOLU sink, aggressive CH₄ mitigation, rapid sulfur decline (early aerosol unmasking).

Well below 1.5°C with high probability. The most ambitious marker and key reference for 1.5°C-compatible pathways.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F01_vl_narrative.png)

</div>
</div>

---

## Narrative: SSP2-L and SSP2-LN — Mitigation and Overshoot

<div class="columns-swf">
<div>

**<span class="scen-l">SSP2-L "Low Emissions"</span>**
*MESSAGEix-GLOBIOM-GAINS 2.1-M-R12*

Middle-of-the-road socioeconomics with strong mitigation. Net-zero CO₂ ~2060–2070. Moderate CDR (BECCS, reforestation). Consistent with well-below-2°C.

<br>

**<span class="scen-ln">SSP2-LN "Low Overshoot"</span>**
*AIM 3.0*

Temporarily exceeds 1.5°C before returning via deep CDR. Tests climate reversibility — high negative emissions by 2070–2100. Connects directly to flat10MIP science questions.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F02_l_ln_narrative.png)

</div>
</div>

---

## Narrative: SSP2-ML and SSP2-M — Current-Policy Range

<div class="columns-swf">
<div>

**<span class="scen-ml">SSP2-ML "Medium-Low Emissions"</span>**
*COFFEE 1.6*

Current NDC ambition plus modest strengthening. Net-zero CO₂ ~2075, moderate CDR. ~2.5°C by 2100 — upper bound of current pledges.

<br>

**<span class="scen-m">SSP2-M "Medium Emissions"</span>**
*IMAGE 3.4*

Limited additional policy beyond current trends. CO₂ peaks and declines slowly. ~3°C by 2100 — a world where ambition does not increase substantially.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F03_ml_m_narrative.png)

</div>
</div>

---

## Narrative: SSP3-H and SSP5-HL — High Emissions and High CDR

<div class="columns-swf">
<div>

**<span class="scen-h">SSP3-H "High Emissions"</span>**
*GCAM 8s*

Regional rivalry, slow energy transition. ~4°C by 2100; warming continues through 2500. The primary high-end scenario for impact research.

<br>

**<span class="scen-hl">SSP5-HL "Very High, then CDR"</span>**
*WITCH 6.0*

Fossil-intensive development through ~2060, then aggressive CDR switch. Peak ~3°C, declining toward ~2.5°C by 2100. The stress-test scenario for late-action CDR and reversibility.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F04_h_hl_narrative.png)

</div>
</div>

---

## SSP2-com: An Updated Pathway for Current Ambition

**Lu et al. (2025)** — *Earth system responses under a global 2°C-target scenario*, ERL 20, 104049

<div class="columns-wf">
<div>

**What SSP2-com represents:**
- SSP2-based scenario updated with mid-century net-zero pledges and CDR deployment
- ~2.05°C by 2100 — sitting **between ML and L** in the ScenarioMIP range
- A reference for AR7 authors relating CMIP7 markers to current stated ambition

**Key message:** SSP2-com illustrates where the trajectory might land if recent net-zero pledges are fulfilled — the marker set brackets the current-policy space well.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F05_ssp2com_comparison.png)

</div>
</div>

---

## Global CO₂ Emissions: All Scenarios to 2100

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F06_all_scenarios_co2e.png)

</div>

<div class="small">

Historical period in black (to 2023). SSP2-com shown as dashed grey for context. Note the wide spread in net-zero timing and post-net-zero CDR reliance across scenarios.

</div>

---

## Non-CO₂ Emissions to 2100

<div class="fig">

![center w:950](../outputs/presentation/F07_ch4_sulfur_2100.png)

</div>

<div class="small">

CH₄ and aerosol forcings contribute substantially to near-term warming spread — partially independent of CO₂ pathway. All scenarios show aerosol (sulfur) decline, causing near-term warming irrespective of CO₂ mitigation ambition.

</div>

---

## Temperature Outcomes 2000–2100

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F08_temperature_2100.png)

</div>

<div class="small">

FaIR v2.2, 1000-member ensemble calibrated to IPCC AR6 assessed ranges. Emissions-driven: carbon cycle uncertainty propagates into temperature spread. SSP2-com sits between ML and L, consistent with current stated ambition.

</div>

---

## Why Extend Beyond 2100?

IAMs provide forcing to 2100 — but many Earth system processes respond on centennial or longer timescales.

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

**CMIP7 request:** Default scenarios should run to 2150, including the 1st 50 years of extension
**CMIP7 requirement:** Scenario forcing to at least **2300**, ideally **2500**, for ocean, ice sheet, and permafrost MIPs.

</div>
</div>

---

## FLEX: Framework for Long-term EXtensions

**Sanderson et al. (in preparation)** — Extends ScenarioMIP emissions beyond 2100 to 2500.

<div class="columns">
<div>

**Design principles:**
- Continuity with IAM narratives — no discontinuities at 2100
- Physically plausible, internally consistent across species
- Configurable via YAML; reproducible, open-source

</div>
<div>

**Pipeline stages:**
CO₂ fossil storyline → AFOLU extension → CDR disaggregation → Non-CO₂ species → FaIR climate simulation

</div>
</div>

<div style="display:flex;align-items:center;justify-content:center;gap:0;margin-top:18px;font-size:14px;">
<div style="background:#eef2ff;border:2px solid #3a5a8a;border-radius:8px;padding:8px 12px;text-align:center;min-width:100px;">
<b>YAML config</b><br/><i style="font-size:12px;">scenarios, targets</i></div>
<div style="font-size:20px;color:#3a5a8a;padding:0 4px;">▶</div>
<div style="background:#f8f9ff;border:1.5px solid #667;border-radius:6px;padding:7px 10px;text-align:center;min-width:90px;">
CO₂ fossil<br/>storyline</div>
<div style="font-size:20px;color:#667;padding:0 4px;">▶</div>
<div style="background:#f8f9ff;border:1.5px solid #667;border-radius:6px;padding:7px 10px;text-align:center;min-width:90px;">
AFOLU<br/>extension</div>
<div style="font-size:20px;color:#667;padding:0 4px;">▶</div>
<div style="background:#f8f9ff;border:1.5px solid #667;border-radius:6px;padding:7px 10px;text-align:center;min-width:90px;">
CDR<br/>disaggregation</div>
<div style="font-size:20px;color:#667;padding:0 4px;">▶</div>
<div style="background:#f8f9ff;border:1.5px solid #667;border-radius:6px;padding:7px 10px;text-align:center;min-width:90px;">
Non-CO₂<br/>species</div>
<div style="font-size:20px;color:#667;padding:0 4px;">▶</div>
<div style="background:#fff8ee;border:2px solid #e07020;border-radius:8px;padding:7px 10px;text-align:center;min-width:100px;">
<b>FaIR v2.2</b><br/><i style="font-size:12px;">841-member ens.</i></div>
<div style="font-size:20px;color:#2e7d32;padding:0 4px;">▶</div>
<div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:8px;padding:8px 10px;text-align:center;min-width:100px;">
<b>Temperature</b><br/>Forcing · Conc.</div>
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

Technology mix at 2100 is inherited from the IAM and held proportionally constant. Total CDR scales with the net CO₂ storyline target.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F10_cdr_aggregate.png)

</div>
</div>

---

## CDR and Storage Limits

![center w:900](external_figures/vanvuuren2026_f03_cdr_top2.png)

<div class="small">

*(Van Vuuren et al. 2026, Fig. 3, VL & L rows)* — Annual and cumulative gross CO₂ fluxes for VL and L markers through 2500. Right panels show cumulative removals against sequestered storage capacity limits (dashed red) and probable fossil reserves (brown).

</div>

---

## AFOLU Beyond 2100: The Carbon-Cycle Inertia Problem

<div class="columns">
<div>

IAMs provide an **AFOLU CO₂ target trajectory** to 2500 — but converting this to consistent **gridded land-use fields** for LUH3 is non-trivial.

**The naïve approach fails:** simply ramping land-use change rates to zero ignores carbon-cycle inertia.

**Why inertia matters:**
- Forests reforested before 2100 continue absorbing CO₂ for decades after planting — **committed removals**
- A naive rate ramp overestimates net AFOLU flux early in the extension period and underestimates it later
- The discrepancy can exceed 200 MtCO₂/yr — material for the global carbon budget and incompatible with FLEX's CO₂ targets

</div>
<div>

![](figures/fig1_afolu_targets.png)

<div class="vsmall">AFOLU target trajectories — what the FLEX extension must reproduce in gridded form. The signal of committed removals from existing forest cohorts must be accounted for in the rate ramp.</div>

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

Once $r(t)$ is solved, it is applied cell-by-cell to the gridded LUH3 state fractions, with per-cell conservation enforced. BECCS biofuel area is scaled independently from the IAM's bioenergy trajectory.

</div>
<div>

![](figures/fig4_extension_verify.png)

<div class="vsmall">Verification: reconstructed AFOLU flux from the extended gridded fields matches the IAM target. A naïve linear ramp diverges substantially in the first post-2100 decades.</div>

</div>
</div>

---

## Non-CO₂ Extensions: CH₄ and Sulfur

<div class="columns-wf">
<div>

**Methane — sigmoid transition to 2500 target:**

Targets set to reflect each scenario's long-term narrative:

| Scenario | 2500 CH₄ target |
|----------|:-----------:|
| <span class="scen-vl">VL</span>, <span class="scen-l">L</span> | 95 Mt/yr |
| <span class="scen-ln">LN</span> | 150 Mt/yr |
| <span class="scen-ml">ML</span> | 120 Mt/yr |
| <span class="scen-m">M</span> | 450 Mt/yr |
| <span class="scen-h">H</span> | 520 Mt/yr |
| <span class="scen-hl">HL</span> | 110 Mt/yr |

**Sulfur** declines in all scenarios (energy decarbonisation). Aerosol unmasking — the warming effect of clean-air policies — is largest in the most ambitious scenarios.

</div>
<div class="fig">

![center w:900](../outputs/presentation/F11_ch4_1750_2500.png)

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

## Temperature Probability Distributions

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F14_temperature_ecdfs.png)

</div>

<div class="small">

The ECDF representation captures the full probabilistic spread for each scenario. Scenario separation increases from 2100 to 2300 — slow carbon cycle feedbacks amplify differences between pathways on centennial timescales.

</div>

---

## WIEMIP: Counterfactual Scenario Pairs

Standard scenario exercises cannot answer **causal** questions about individual policy levers.

<div class="highlight">

*"How much additional sea level rise is committed by an overshoot trajectory, compared to maintaining the same peak warming level?"*

</div>

A core AR7-WG1-CH9 question. Answering it requires two scenarios **identical in all respects except CO₂ pathway**. FLEX enables this by **optimising extension parameters to hit a prescribed temperature target**, holding all non-CO₂ forcing fixed.

---

## WIEMIP Design: Source and Counterfactual Pairs

**Three scenario pairs, each sharing non-CO₂ forcing:**

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

## WIEMIP Results: CO₂ Emissions

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F15_wiemip_co2_emissions.png)

</div>

<div class="small">

The CF pathway deploys CDR earlier and more deeply to suppress the overshoot. Non-CO₂ forcing is identical between source and CF — any difference in climate response is attributable to this CO₂ pathway difference alone.

</div>

---

## WIEMIP Results: Temperature Outcomes

<div class="fig fig-tall">

![center w:950](../outputs/presentation/F16_wiemip_temperature.png)

</div>

<div class="small">

The optimised CF variants track their prescribed targets. Residual uncertainty (shading) reflects carbon cycle and climate sensitivity spread — not CO₂ pathway uncertainty, which is removed by construction.

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

**ScenarioMIP-CMIP7 scenario set:**
- Seven markers spanning ~1.5°C to ~4°C; emissions-driven as primary protocol
- Includes overshoot (LN), high-CDR stress-test (HL), and current-policy-range (ML, M) markers
- SSP2-com sits between ML and L — a useful reference for current stated ambition

**Emissions-driven protocol:**
- Carbon cycle feedbacks correctly represented in temperature spread
- flat10MIP constrains TCRE and asymmetric response — use these results when interpreting overshoot scenarios; recovery is slower than the rise

</div>
<div>

**FLEX extensions (1750–2500):**
- Consistent CO₂, AFOLU (LUH3-compatible), CDR, and non-CO₂ forcing beyond 2100
- Carbon-cycle-consistent AFOLU ramp avoids flux errors from naive rate ramps

**WIEMIP counterfactuals:**
- Designed for WG1-CH9: overshoot vs. maintain-peak-warming
- Clean experimental design — non-CO₂ forcing held constant; temperature difference attributable solely to CO₂ pathway
- Framework extensible to any temperature target or scenario pairing

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

**Benjamin Sanderson** · CICERO, Oslo · benjamin.sanderson@cicero.oslo.no

*FLEX codebase: github.com/benmsanderson/FLEX (link TBC)*

---

<!-- _paginate: false -->

## Appendix A1: FLEX Extension Parameters

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

## Appendix A2: FaIR v2.2 Configuration

<div class="columns">
<div>

**Ensemble setup:**
- 1000-member probabilistic ensemble
- Parameters calibrated to IPCC AR6 assessed ranges (ECS, TCR, TCRE)
- Emissions-driven: CO₂, CH₄, N₂O, halocarbons, SO₂, BC, OC, ozone precursors
- Run period: 1750–2500 for all scenarios

**Key outputs:**
- Temperature (median, 5th, 95th percentile)
- Total and species-resolved radiative forcing
- CO₂, CH₄, N₂O concentrations
- CO₂-equivalent emissions (AR6 GWP100)
- ECDF data for probabilistic impact assessment

</div>
<div class="fig">

[FIG: FaIR calibration — ECS and TCR distributions vs. AR6 assessed likely ranges]
*(from FaIR documentation / Smith et al. 2021)*

</div>
</div>

---

<!-- _paginate: false -->

## Appendix A3: Extensions 8-Panel Diagnostic

<div class="fig fig-tall">

[FIG: 8-panel extensions diagnostic for scenariomip_default — CO₂ FFI, CO₂ AFOLU, CH₄, cumulative CO₂, Sulfur, total CO₂e, total forcing, temperature anomaly — all 1750–2500, all 7 scenarios]
*(existing: outputs/scenariomip_default/ — extensions.png from 5202_extension_fair_plots)*

</div>

---

## flat10MIP: Key Results

<div class="columns-wf">
<div>

**Multi-model ensemble shows:**

- **Warming phase:** large spread in peak temperature — TCRE uncertainty across ESMs
- **Zero-emissions phase:** temperature plateaus but does not reverse
- **Negative-emissions phase:** temperature declines **more slowly** than it rose — asymmetric response from ocean heat uptake and land carbon lag
- **For ScenarioMIP:** overshoot scenarios won't recover as quickly as simplified frameworks suggest

</div>
<div class="fig">

![center w:900](external_figures/sanderson2025_f03_flat10mip_temperature.png)
*(Sanderson et al. 2025, Fig. 3)*

</div>
</div>