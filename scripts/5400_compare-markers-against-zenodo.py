# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import matplotlib.pyplot as plt
import pandas as pd
import pandas_indexing as pix
import pandas_openscm
import pandas_openscm.io
import sys

# %%
#pandas_openscm.register_pandas_accessor()

# %%
# Downloaded from https://zenodo.org/records/18497404
em_harm_dir = "../../emissions_harmonization_historical/"
#sys.exit(4)
# %%
local_result = pd.read_csv(f"../outputs/continuous_emissions_timeseries_1750_2500.csv", index_col=[0, 1, 2, 3, 4,5])
print(local_result.head(2))
#sys.exit(4)

local_result_extentsion = pd.read_csv(f"{em_harm_dir}/notebooks/continuous_emissions_timeseries_1750_2500.csv", index_col=[0, 1, 2, 3, 4, 5])
local_result_extension = local_result_extentsion.loc[pix.ismatch(variable="**Emissions**")]
for col in local_result_extension.columns:
    if col < local_result.columns[0] or col > local_result.columns[-1]:
        local_result_extension = local_result_extension.drop(columns=col)

#sys.exit(4)
# Compare with what is in the extensions database,
# should be the same as the zenodo data for the overlapping variables and years
print("Comparing local results from infilled extensions database with Zenodo data...")
compare_df = pix.concat(
    [
        local_result_extension.reset_index("scenario", drop=True).pix.assign(source="local_em_harm"),
        local_result.reset_index("scenario", drop=True).pix.assign(source="flex"),
    ]
).sort_index(axis=1)

for model, mdf in compare_df.groupby(["model"]):
    print(f"Checking {model}")
    for variable, ts_df in mdf.groupby("variable"):
        # print(variable)
        if "local" not in ts_df.index.get_level_values("source"):
            continue

        tmp = ts_df.dropna(how="all", axis="columns")
        try:
            pd.testing.assert_frame_equal(
                tmp.loc[pix.isin(source="local")].reset_index(["source", "unit"], drop=True),
                tmp.loc[pix.isin(source="zenodo")].reset_index(["source", "unit"], drop=True),
                rtol=1e-5,
                atol=1e-6,
            )
        except AssertionError as exc:
            print(exc)
            print(f"Model: {model}, Variable: {variable}")
            print(tmp.loc[pix.isin(source="local")])
            print(tmp.loc[pix.isin(source="zenodo")])
            ax = tmp.pix.project(["source", "model", "variable", "unit"]).T.plot()
            ax.legend(loc="center left", bbox_to_anchor=(1.05, 0.5))
            plt.show()
