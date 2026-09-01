"""Convert a published ScenarioMIP release spreadsheet into the CSV the pipeline reads.

The marker scenarios are published as a single spreadsheet
(https://doi.org/10.5281/zenodo.19825038, release v0.2), while this pipeline
reads `data/scenarios_complete_global.csv` in IAMC wide CSV format. The two
differ in three ways, all handled here:

  * the release prefixes every series with
    "Climate Assessment|Harmonized and Infilled|", which is stripped;
  * the release names scenarios "Very Low - SSP1 (Marker)" where the configs use
    "SSP1 - Very Low Emissions", so scenarios are renamed. The mapping is derived
    from the model column, which is identical in both and pairs 1:1 with the
    scenario, rather than by parsing scenario strings;
  * the release starts in 2000 and the pipeline expects the scenario period only,
    so year columns before --from-year are dropped.

Usage
-----
    pixi run python scripts/convert_scenario_release.py \\
        ScenarioMIP_emissions_marker_scenarios_v0.2.xlsx

Writes data/scenarios_complete_global.csv. See data/README.md for where to get
the spreadsheet.

REGIONAL DATA IS NOT IN THE PUBLISHED RELEASE. The spreadsheet is World-only, so
this script cannot produce `data/scenarios_regional.csv`. Configurations that
need the regional breakdown require the regional delivery, requested through the
ScenarioMIP Explorer.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Mirrors flex.config: FLEX_DATA_DIR relocates the inputs outside the repository.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FLEX_DATA_DIR") or REPO_ROOT / "data").expanduser()

PREFIX = "Climate Assessment|Harmonized and Infilled|Emissions|"

# Fallback used only when the config cannot be imported. The pipeline's scenario
# names, keyed by the model that produced them.
FALLBACK_BY_MODEL = {
    "REMIND-MAgPIE 3.5-4.11": "SSP1 - Very Low Emissions",
    "AIM 3.0": "SSP2 - Low Overshoot_a",
    "MESSAGEix-GLOBIOM-GAINS 2.1-M-R12": "SSP2 - Low Emissions",
    "COFFEE 1.6": "SSP2 - Medium-Low Emissions",
    "IMAGE 3.4": "SSP2 - Medium Emissions",
    "GCAM 8s": "SSP3 - High Emissions",
    "WITCH 6.0": "SSP5 - Medium-Low Emissions_a",
}

# Aggregates the release carries that the pipeline does not consume. Kept out so
# the CSV matches what the extension code expects to iterate over.
DROP_VARIABLES = {
    "Emissions|CO2",
    "Emissions|GHG AR6GWP100",
    "Emissions|Kyoto GHG AR6GWP100",
}


def scenario_by_model(config_name):
    """Map model -> pipeline scenario name, preferring the config over the fallback."""
    try:
        from flex.config import load_config
        cfg = load_config(config_name)
    except Exception as exc:                                    # noqa: BLE001
        print(f"  note: using built-in scenario names ({type(exc).__name__}: {exc})")
        return dict(FALLBACK_BY_MODEL)
    mapping = {}
    for scenario, model, *_ in cfg.scenario_model_match.values():
        mapping[model] = scenario
    return mapping


def convert(xlsx, out, config_name, from_year, keep_aggregates):
    df = pd.read_excel(xlsx, sheet_name="data")

    missing = {"model", "scenario", "region", "variable", "unit"} - set(df.columns)
    if missing:
        sys.exit(f"error: sheet 'data' is missing column(s): {sorted(missing)}")

    emis = df[df["variable"].astype(str).str.startswith(PREFIX)].copy()
    if emis.empty:
        sys.exit(f"error: no variables start with {PREFIX!r}. Is this a ScenarioMIP "
                 "release spreadsheet?")
    emis["variable"] = "Emissions|" + emis["variable"].str.removeprefix(PREFIX)

    if not keep_aggregates:
        emis = emis[~emis["variable"].isin(DROP_VARIABLES)]

    by_model = scenario_by_model(config_name)
    unknown = sorted(set(emis["model"]) - set(by_model))
    if unknown:
        print(f"  warning: no scenario name known for model(s) {unknown}; "
              "their release names are kept unchanged")
    emis["scenario"] = [by_model.get(m, s) for m, s in zip(emis["model"], emis["scenario"])]

    years = sorted(c for c in emis.columns if str(c).isdigit())
    keep = [y for y in years if int(y) >= from_year]
    dropped = len(years) - len(keep)
    emis = emis[["model", "scenario", "region", "variable", "unit"] + keep]

    regions = sorted(set(emis["region"].astype(str)))
    out.parent.mkdir(parents=True, exist_ok=True)
    emis.to_csv(out, index=False)

    print(f"\nWrote {out}")
    print(f"  rows       {len(emis)}")
    print(f"  scenarios  {emis['scenario'].nunique()}")
    print(f"  variables  {emis['variable'].nunique()}")
    print(f"  years      {keep[0]}-{keep[-1]}  ({dropped} earlier column(s) dropped)")
    print(f"  regions    {regions}")

    if regions == ["World"]:
        print("\n  Global data only. The published release contains no regional")
        print("  breakdown, so data/scenarios_regional.csv cannot be produced from it.")
        print("  Configurations needing regional output require the regional delivery")
        print("  from https://scenariomip.apps.ece.iiasa.ac.at - see data/README.md.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx", type=Path, help="the release spreadsheet")
    ap.add_argument("-o", "--out", type=Path,
                    default=DATA_DIR / "scenarios_complete_global.csv",
                    help="output CSV (default: data/scenarios_complete_global.csv)")
    ap.add_argument("--config", default="scenariomip_default",
                    help="config whose scenario names to target")
    ap.add_argument("--from-year", type=int, default=2023,
                    help="drop year columns before this (default: 2023)")
    ap.add_argument("--keep-aggregates", action="store_true",
                    help="keep Emissions|CO2 and the GHG aggregates")
    args = ap.parse_args()

    if not args.xlsx.exists():
        sys.exit(f"error: {args.xlsx} not found. See data/README.md for the download.")
    convert(args.xlsx, args.out, args.config, args.from_year, args.keep_aggregates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
