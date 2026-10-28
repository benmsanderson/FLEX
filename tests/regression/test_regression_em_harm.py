"""Check FLEX reproduces the extensions from the CMIP7 emissions harmonization pipeline.

Compares the outputs of notebooks/5191_extension.py against those written by
notebooks/5191_extension.py in iiasa/emissions_harmonization_historical. Both
runs have to be made first, on the same inputs. The em-harm checkout is looked
for in EM_HARM_DIR, defaulting to a sibling of this repository.
"""

import os

import pandas as pd
import pytest

here = os.path.dirname(os.path.abspath(__file__))

FLEX_OUTPUTS = os.path.join(here, "..", "..", "outputs")
EM_HARM_DIR = os.environ.get("EM_HARM_DIR") or os.path.join(here, "..", "..", "..", "emissions_harmonization_historical")
EM_HARM_OUTPUTS = os.path.join(os.path.expanduser(EM_HARM_DIR), "notebooks")


def load_pair(filename):
    flex_csv = os.path.join(FLEX_OUTPUTS, filename)
    orig_csv = os.path.join(EM_HARM_OUTPUTS, filename)
    for path in (flex_csv, orig_csv):
        if not os.path.exists(path):
            pytest.skip(f"{path} not found; run both 5191_extension notebooks first")

    df_flex = pd.read_csv(flex_csv, index_col=[0, 1, 2, 3, 4, 5])
    df_orig = pd.read_csv(orig_csv, index_col=[0, 1, 2, 3, 4, 5])
    print(df_flex.shape)
    print(df_orig.shape)
    return df_flex, df_orig


@pytest.mark.parametrize(
    "filename",
    [
        "continuous_emissions_timeseries_1750_2500.csv",
        "extensions_full_emissions_timeseries_2023_2500.csv",
    ],
)
def test_matches_em_harm(filename):
    df_flex, df_orig = load_pair(filename)
    pd.testing.assert_frame_equal(df_flex, df_orig, rtol=1e-5, atol=1e-6)
