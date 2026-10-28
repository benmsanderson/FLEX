# Changelog

## 1.0.0 - 2026-10-28

First release: the extension of the CMIP7 ScenarioMIP marker scenarios to 2500,
as used in the CMIP7 emissions harmonization pipeline.

- Extension functions in `src/flex`, refactored out of
  `emissions_harmonization_historical.extensions`, and the extension notebook
  `notebooks/5191_extension.py`, which reads CSV inputs instead of the
  pipeline's databases.
- Fix `extend_flat_evolution` and `extend_flat_cumulative`, which built a
  0-d integer array (`np.zeros_like(len(...))`); neither is used by the
  extension notebook.
- The notebook finds `data/` and `outputs/` relative to the repository, so
  `python notebooks/5191_extension.py` works from the repository root, and
  honours `FLEX_DATA_DIR`.
- Regression test against the harmonization pipeline's outputs
  (`tests/regression`), with the pipeline checkout located via `EM_HARM_DIR`.
- ScenarioMIP scenario data are no longer distributed; `scripts/fetch_data.py`
  checks inputs and `scripts/convert_scenario_release.py` converts the open
  v0.2 release. `FLEX_DATA_DIR` relocates the inputs.
