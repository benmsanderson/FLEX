import os

import pandas as pd
import pandas.testing as pdt


here = os.path.dirname(os.path.abspath(__file__))

def test_global_output_csv():

    global_output_csv = os.path.join(here, "..", "..", "outputs", "continuous_emissions_timeseries_1750_2500.csv")
    orig_output_csv = os.path.join(here, "..", "..", "..","emissions_harmonization_historical", "notebooks", "continuous_emissions_timeseries_1750_2500.csv")

    if not os.path.exists(global_output_csv):
        raise FileNotFoundError(f"Global output CSV not found at {global_output_csv}")
    if not os.path.exists(orig_output_csv):
        raise FileNotFoundError(f"Original output CSV not found at {orig_output_csv}")
    
    df_global = pd.read_csv(global_output_csv, index_col=[0, 1, 2, 3, 4, 5])
    df_orig = pd.read_csv(orig_output_csv, index_col=[0, 1, 2, 3, 4, 5])

    print(df_global["2024.0"].head())
    print(df_orig["2024.0"].head())
    print(df_global.shape)
    print(df_orig.shape)
    try:
        pd.testing.assert_frame_equal(df_global, df_orig, rtol=1e-5, atol=1e-6)
    except AssertionError as e:
        print("DataFrames are not equal:")
        print(e)
        raise


def test_regional_output_csv():

    regional_output_csv = os.path.join(here, "..", "..", "outputs", "extensions_full_emissions_timeseries_2023_2500.csv")
    orig_output_csv = os.path.join(here, "..", "..", "..","emissions_harmonization_historical", "notebooks", "extensions_full_emissions_timeseries_2023_2500.csv")

    if not os.path.exists(regional_output_csv):
        raise FileNotFoundError(f"Regional output CSV not found at {regional_output_csv}")
    if not os.path.exists(orig_output_csv):
        raise FileNotFoundError(f"Original output CSV not found at {orig_output_csv}")
    
    df_regional = pd.read_csv(regional_output_csv, index_col=[0, 1, 2, 3, 4, 5])
    df_orig = pd.read_csv(orig_output_csv, index_col=[0, 1, 2, 3, 4, 5])

    print(df_regional["2024.0"].head())
    print(df_orig["2024.0"].head())
    print(df_regional.shape)
    print(df_orig.shape)


    pd.testing.assert_frame_equal(df_regional, df_orig, rtol=1e-5, atol=1e-6)