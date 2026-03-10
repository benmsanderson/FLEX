import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))

#global_output_csv = os.path.join(here, "..", "outputs", "continuous_emissions_timeseries_1750_2500.csv")
#orig_output_csv = os.path.join(here, "..", "..", "emissions_harmonization_historical", "notebooks", "continuous_emissions_timeseries_1750_2500.csv")
global_output_csv = os.path.join(here, "..", "notebooks", "debug_scenarios_regional.csv")
orig_output_csv = os.path.join(here, "..", "..", "emissions_harmonization_historical", "notebooks", "debug_scenarios_regional_before_extension.csv")

df_global = pd.read_csv(global_output_csv, index_col=[0, 1, 2, 3, 4, 5])
df_orig = pd.read_csv(orig_output_csv, index_col=[0, 1, 2, 3, 4, 5])
print(df_global.head())
# Compare rows and plot mismatches
rtol = 1e-5
mismatches = []

for idx in df_global.index:
    print(idx)
    if idx in df_orig.index:
        global_row = df_global.loc[idx].values
        orig_row = df_orig.loc[idx].values
        
        # Check if values are nearly equal
        if not np.allclose(global_row, orig_row, rtol=rtol, atol=0):
            mismatches.append({
                'index': idx,
                'global': global_row,
                'orig': orig_row
            })

# Plot mismatches
if mismatches:
    print(f"Found {len(mismatches)} mismatches with rtol={rtol}")
    
    for i, mismatch in enumerate(mismatches):  # Plot first 10 mismatches
        idx = mismatch['index']
        # Extract index components (assuming order: model, variable, unit, ...)
        print(idx)
        print(mismatch['global'])
        print(mismatch['orig'])
        model = idx[0]
        variable = idx[4]
        unit = idx[5]
        
        # Get column names (years) for x-axis
        years = df_global.columns.values.astype(float)
        
        fig, ax = plt.subplots()
        ax.plot(years, mismatch['global'], label='Global')
        ax.plot(years, mismatch['orig'], label='Original')
        ax.set_title(f"Mismatch: {model} - {variable}")
        ax.set_xlabel("Year")
        ax.set_ylabel(unit)
        ax.legend()
        
        # Filename with model and variable
        filename = f"mismatch_{model}_{variable}_{i}.png"
        plt.savefig(filename)
        plt.close()
else:
    print("All rows match within tolerance!")