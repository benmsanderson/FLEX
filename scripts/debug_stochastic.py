from fair import FAIR
from fair.io import read_properties
import pandas as pd
import inspect

f = FAIR()
f.define_time(1750, 2501, 1)
f.define_scenarios(['test'])
species, properties = read_properties('data/fair-inputs/species_configs_properties_1.4.1.csv')
f.define_species(species, properties)
df_params = pd.read_csv('data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv', index_col=0)
f.define_configs(df_params.index)
f.allocate()

# Check params before override
print("Params CSV columns (first 15):")
print(df_params.columns.tolist()[:15])
print("\nParams CSV stochastic columns:")
stoch_cols = [c for c in df_params.columns if 'stoch' in c.lower() or 'seed' in c.lower()]
print(stoch_cols)
if stoch_cols:
    print("\nValues in stochastic columns:")
    for col in stoch_cols:
        print(f"  {col}: {df_params[col].unique()}")

f.override_defaults('data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv')

# Check what override created
print("\n\nAfter override_defaults, checking for stochastic attributes:")
print("Direct attributes:", [a for a in dir(f) if 'stoch' in a.lower() or 'seed' in a.lower()])

# Check for climate configs or other config structures
print("\n\nChecking for climate_configs:")
if hasattr(f, 'climate_configs'):
    print(f"  Type: {type(f.climate_configs)}")
    print(f"  Keys (first 20): {list(f.climate_configs.keys())[:20]}")
    # Check if stochastic params are there
    stoch_keys = [k for k in f.climate_configs.keys() if 'stoch' in k.lower() or 'seed' in k.lower() or 'use_seed' in k.lower()]
    print(f"  Stochastic-related keys: {stoch_keys}")
    if stoch_keys:
        for key in stoch_keys:
            val = f.climate_configs[key]
            print(f"\n  {key}:")
            print(f"    Type: {type(val)}")
            if hasattr(val, 'shape'):
                print(f"    Shape: {val.shape}")
                print(f"    Values: {val.values if hasattr(val, 'values') else val}")
                
                # Try modifying
                print(f"    Trying to set to False...")
                try:
                    f.climate_configs[key][:] = False
                    print(f"    Success! New values: {f.climate_configs[key].values}")
                except Exception as e:
                    print(f"    Failed: {e}")

# Check if there's a run method parameter  
print(f"\n\nFAIR.run signature: {inspect.signature(f.run)}")

# Look for other related parameters/attributes
print("\n\nLooking for anything 'seed' related:")
for attr in dir(f):
    if 'seed' in attr.lower() and not attr.startswith('_'):
        val = getattr(f, attr)
        print(f"  {attr}: {type(val)}")

# Let's check the source code docstring
print("\n\nFAIR.run docstring:")
if f.run.__doc__:
    print(f.run.__doc__[:500])

# Check fill_from_rcmip signature
import inspect
print("\n\nFAIR methods with 'run' in name:")
methods = [m for m in dir(f) if 'run' in m.lower() and not m.startswith('_')]
for m in methods:
    method = getattr(f, m)
    if callable(method):
        try:
            sig = inspect.signature(method)
            print(f"  {m}{sig}")
        except:
            pass
