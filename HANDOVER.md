# Handover: FLEX v1.0.0 for Zeb's ScenarioMIP paper / gcages docs

Working notes, 2026-10-28. Delete this file before merging to `main`.

## Context

Zeb Nicholls wants to include FLEX in the gcages docs
(<https://gcages.readthedocs.io/en/latest/how-to-guides/how-to-run-the-cmip7-scenariomip-workflow/>)
and asked:

1. Are we happy for FLEX to be run in those docs?
2. Is there a release or PyPI package, or just latest `main`?
3. Is the extended emissions dataset on Zenodo, for his double check?

## State of this branch (`claude/festive-ritchie-3uux76`)

Two commits on top of `main` (f8c78e9), pushed, no PR yet:

- **96f8f3f** Prepare v1.0.0: README and `data/README.md` cleanup (removed
  references to other branches: `flex.config`, FaIR inputs, `vl-frankenstein`),
  the notebook resolves `data/`/`outputs/` from the repo root and honours
  `FLEX_DATA_DIR` (before, running it from the repo root looked one directory
  too high), the regression test reads `EM_HARM_DIR` and skips cleanly, two
  broken debug scripts removed, `CITATION.cff`, `.zenodo.json`, `CHANGELOG.md`,
  version 1.0.0.
- **57ff387** Declare `scipy` in `pixi.toml` (was only transitive). `pixi.lock`
  deliberately left unchanged: the lock already has scipy 1.17.1, and
  re-locking with pixi 0.83 would rewrite it to lock format v7.

## What has been verified

- **Code equivalence with em-harm** (static diff against
  `iiasa/emissions_harmonization_historical` at ca80efc): the `src/flex`
  modules are em-harm's `extensions` package plus wrapper functions that
  contain the notebook's former inline code unchanged. The only code change is
  `np.zeros_like(len(...))` → `np.zeros(...)` in `extend_flat_evolution` and
  `extend_flat_cumulative`, neither of which is called.
- `pixi install --frozen` and `pixi run test` work (tests skip: no outputs).
- `scripts/convert_scenario_release.py` converts the public v0.2 xlsx (364
  rows, 7 scenarios, 52 variables, 2023-2100).
- Notebook runs as far as loading the inputs, then stops at the missing
  `scenarios_regional.csv`.

## Regression run: passed (2026-10-28, on the CICERO machine)

Both regression tests pass, and both output files are bit-for-bit identical to
em-harm (max abs diff 0.0): `continuous_emissions_timeseries_1750_2500.csv`
(378 x 751) and `extensions_full_emissions_timeseries_2023_2500.csv`
(16795 x 478).

How it was run:

- Inputs: the `desc-paper` scenario files (sha256 `45353da8…`, `9f8a56b1…`)
  plus `main` history. The v0.1 `main` scenario files (`d0eefa77…`,
  `2976247f…`) are not on this machine. That doesn't matter for an
  equivalence check: both pipelines read the same inputs.
- em-harm baseline: a clean worktree at ca80efc, run in em-harm's own pixi
  env (pandas 2.2.3, pandas-openscm 0.5.1; FLEX uses pandas 3.0.1,
  pandas-openscm 0.9.1). The only patch: the database loads swapped for
  FLEX's CSV-loading block verbatim, and the database writes stubbed.
- Don't use em-harm's local `HEAD` (f4363d2) as the baseline. It changes
  `np.zeros(len(extended_years))` to `np.zeros_like(extended_years)` in
  `extend_co2_for_scen_storyline`, which makes the fossil-CO2 array
  integer-typed.

Also fixed: the notebook wrote three intermediate CSVs into the current
directory (the repo root when run as documented). They now go to `outputs/`.

## To do

1. ~~Run the regression check.~~ Done, see above.
2. Open a PR to `main`, merge (drop this file first).
3. Enable the repo at <https://zenodo.org/account/settings/github>, then create
   GitHub release `v1.0.0`. Fix the date in `CITATION.cff` and
   `CHANGELOG.md` if it is not 2026-10-28.
4. README "Contact" lists only Ben; consider adding Marit.
5. Decide whether and where to deposit the extended (1750-2500) marker
   emissions as a dataset. Not on Zenodo now: the FLEX DOI
   10.5281/zenodo.22212710 holds only the preprint PDFs. Licence follows
   IIASA's terms for the scenarios; possibly better as part of em-harm's next
   Zenodo release. Agree with Zeb.
6. Reply to Zeb (draft below), adding the software DOI once it exists.

## Facts for the reply

- FLEX software release: none yet; v1.0.0 prepared on this branch.
- Extended dataset on Zenodo: no. He should use the file Ben sent.
- Public inputs alone cannot run FLEX: v0.2 (10.5281/zenodo.19825038) is
  World-only, 2000-2100, and the notebook needs the regional harmonised
  scenarios. Within the gcages workflow this is fine: the harmonised
  regional data exist before the extension step.
- The em-harm v0.1 record (10.5281/zenodo.18497404) has no public files.

## Draft reply to Zeb

> Hi Zeb — yes, very happy for FLEX to go in the gcages docs, and the contact
> info is right. We're tagging a v1.0.0 release with a Zenodo DOI so you have
> something to pin; until then use `main` of benmsanderson/FLEX. The code is a
> refactor of em-harm's `5191_extension.py`, and the outputs match the em-harm
> run to rtol 1e-5. The extended emissions dataset isn't on Zenodo yet (the
> 10.5281/zenodo.22212710 record is just the preprint), so please use the file
> I sent for your double check. We'll let you know once a dataset DOI exists.
> Ben

Step 1 passed: the outputs are bit-for-bit identical, so the reply can say
"reproduce the em-harm run exactly" rather than "to rtol 1e-5".

## Cloud sessions

Pixi isn't preinstalled. Add to the environment setup script:

```bash
mkdir -p ~/.pixi/bin && curl -fsSL https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-unknown-linux-musl.tar.gz | tar xz -C ~/.pixi/bin
export PATH="$HOME/.pixi/bin:$PATH"
```
