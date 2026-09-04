"""Obtain and verify the input data FLEX needs.

The ScenarioMIP scenario files are not redistributable and so are not stored in
this repository; you have to download them yourself. The historical files do
ship here. See data/README.md for the source and terms of each.

This script does three things:

  * downloads the inputs that can be fetched automatically (FaIR parameters),
  * checks that the scenario files you supplied are present and readable,
  * verifies everything against the SHA-256 it had when the pipeline was built.

Usage
-----
    pixi run python scripts/fetch_data.py            # fetch what is fetchable, then check
    pixi run python scripts/fetch_data.py --check    # check only, no downloads
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Mirrors flex.config: FLEX_DATA_DIR relocates the inputs outside the repository.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FLEX_DATA_DIR") or REPO_ROOT / "data").expanduser()

# Mirrors flex.config.FAIR_* — keep the two in step. This script has to run
# before the package is importable, so the constants are repeated rather than
# imported. 1.6.0 is Zenodo record 18828694; the version-specific record DOI is
# used instead of the concept DOI (10.5281/zenodo.7112539) so the fetch stays
# reproducible once a later calibration is published.
FAIR_CALIBRATION_VERSION = "1.6.0"
FAIR_CALIBRATION_DOI = "10.5281/zenodo.18828694"
FAIR_PARAMS_FILE_NAME = "calibrated_constrained_parameters.csv"
FAIR_PARAMS_FILE_HASH = "md5:b0fadc337e7b66525703f5b7f5fce2db"

# SHA-256 of each input as the pipeline was developed against it. Several
# branches were built on different releases of the upstream datasets, so more
# than one hash can be legitimate; each is labelled with where it was used. An
# unlisted hash is not an error, it just means a release nobody here has run.
# Files you must obtain yourself; see data/README.md.
MUST_OBTAIN = ("scenarios_complete_global.csv", "scenarios_regional.csv")

KNOWN = {
    "scenarios_complete_global.csv": [
        ("d0eefa7773e757e260bc900d08f5965a680a5040bd62d28df6ade8f6c2189bdc", "main"),
        ("45353da846e86a1d667ff8367d4fe4f716f17e33c1ab9df52cf6028ee27d78f2", "desc-paper"),
        ("5b7715dd02636938401b016a7a412ceb5b0ab99278bf3addad5d1325994e4546", "integer-bug-fix-ms"),
    ],
    "scenarios_regional.csv": [
        ("2976247f794c70eb4ea81a1cce20c0a20eb70ca008618731d2e87c8a1072c0e2", "main"),
        ("9f8a56b10f06c7981091c9029648a7a6374092cd116f8a2c95e1c7d2636091e4", "desc-paper"),
        ("6844630fab048b2ccebab195512834167dcfb2c6f0488e8da9a028d0a355c01b", "integer-bug-fix-ms"),
    ],
    "history.csv": [
        ("ca7bab9989a3ab949c6301d00927e56f04b8a85391c8b89221bd87e944262401", "main"),
        ("733f3293a1be5f8da9c069412cac03547cec72618610758b7dd32708fbbd890f", "integer-bug-fix-ms"),
    ],
    "history_regional.csv": [
        ("2fb43a236ba56b6a72afb322366c20b62eb761fa22f24914d529156849709913", "main"),
        ("462c1e67818bc3d06348822c3e3de236a02aff0f5cea6d1c9b84270d3aad050f", "integer-bug-fix-ms"),
    ],
}

SCENARIO_SOURCE = (
    "ScenarioMIP Explorer, https://scenariomip.apps.ece.iiasa.ac.at\n"
    "      Open release v0.2: https://doi.org/10.5281/zenodo.19825038\n"
    "      Note v0.2 is a spreadsheet and adds the ML marker; this pipeline was\n"
    "      built on the v0.1 CSV delivery, so conversion is needed and results\n"
    "      will not reproduce the published run exactly. See data/README.md."
)

WHERE_FROM = {
    "scenarios_complete_global.csv": SCENARIO_SOURCE,
    "scenarios_regional.csv": SCENARIO_SOURCE,
    "history.csv": "Ships with this repository via Git LFS; run `git lfs pull`.",
    "history_regional.csv": "Ships with this repository via Git LFS; run `git lfs pull`.",
}

# Only vl-frankenstein needs these, so their absence is a warning, not an error.
OPTIONAL_DIRS = {
    "vl-extensions-inputs": "Bespoke deliveries; request from the scenario providers.",
}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def looks_like_lfs_pointer(path):
    """Old clones may still hold 130-byte LFS stubs rather than real data."""
    if path.stat().st_size > 1024:
        return False
    with open(path, "rb") as fh:
        return fh.read(40).startswith(b"version https://git-lfs")


def fetch_fair_inputs():
    """Download the FaIR calibrated-constrained parameters if not present."""
    rel = f"fair-inputs/{FAIR_CALIBRATION_VERSION}/{FAIR_PARAMS_FILE_NAME}"
    target = DATA_DIR / "fair-inputs" / FAIR_CALIBRATION_VERSION / FAIR_PARAMS_FILE_NAME
    if target.exists():
        print(f"  ok       {rel} (already present)")
        return
    try:
        import pooch
    except ImportError:
        print("  SKIP     pooch not installed; cannot fetch FaIR parameters")
        return
    print(f"  fetching FaIR {FAIR_CALIBRATION_VERSION} calibrated-constrained "
          "parameters from Zenodo ...")
    pooch.create(
        path=str(DATA_DIR / "fair-inputs"),
        base_url=f"doi:{FAIR_CALIBRATION_DOI}",
        version=FAIR_CALIBRATION_VERSION,
        registry={FAIR_PARAMS_FILE_NAME: FAIR_PARAMS_FILE_HASH},
    ).fetch(FAIR_PARAMS_FILE_NAME)
    print(f"  ok       {target}")


def report(name, missing):
    """Print the state of one input file; record it if unusable."""
    p = DATA_DIR / name
    if not p.exists():
        print(f"  MISSING  data/{name}")
        print(f"      from: {WHERE_FROM[name]}")
        missing.append(name)
        return
    if looks_like_lfs_pointer(p):
        print(f"  POINTER  data/{name} is a Git LFS stub, not real data")
        if name in MUST_OBTAIN:
            print("      This clone predates the data removal. Obtain the real file:")
            print(f"      {WHERE_FROM[name]}")
        else:
            print("      Run `git lfs install && git lfs pull` to materialise it.")
        missing.append(name)
        return
    digest = sha256(p)
    match = next((label for h, label in KNOWN[name] if h == digest), None)
    if match:
        print(f"  ok       data/{name}  (matches the version used on {match})")
    else:
        print(f"  UNKNOWN  data/{name}")
        print(f"      sha256 {digest}")
        print("      Not a release this pipeline has been run against. Expected if you"
              " converted the")
        print("      open v0.2 spreadsheet; see data/README.md for how far it differs"
              " from v0.1.")


def check():
    missing = []

    print("\nScenario files - you supply these:")
    for name in MUST_OBTAIN:
        report(name, missing)

    print("\nHistorical files - shipped with this repository:")
    for name in KNOWN:
        if name not in MUST_OBTAIN:
            report(name, missing)

    print("\nOptional inputs:")
    for name, note in OPTIONAL_DIRS.items():
        p = DATA_DIR / name
        present = p.is_dir() and any(p.iterdir())
        print(f"  {'ok      ' if present else 'absent  '} data/{name}/")
        if not present:
            print(f"      Only needed by the vl-frankenstein config. {note}")

    return missing


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify existing files only; do not download anything")
    args = ap.parse_args()

    print(f"Data directory: {DATA_DIR}"
          f"{'  (from FLEX_DATA_DIR)' if os.environ.get('FLEX_DATA_DIR') else ''}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not args.check:
        print("Automatically fetchable inputs:")
        fetch_fair_inputs()

    missing = check()

    if missing:
        print(f"\n{len(missing)} input file(s) unusable. See data/README.md for how to "
              "obtain each one.")
        return 1
    print("\nAll required inputs present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
