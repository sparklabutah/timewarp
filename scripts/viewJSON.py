import json
import pandas as pd

# Load the JSON file
with open('data/web_policy_sft.json', 'r') as f:
    data = json.load(f)

# Check what's inside
print(f"Loaded type: {type(data)}")

if isinstance(data, list):
    print(f"Number of items: {len(data)}")
    if data:
        print(f"First item type: {type(data[0])}")
        if isinstance(data[0], dict):
            print(f"Keys in first item: {list(data[0].keys())}")
            print("\nFirst item:")
            print(json.dumps(data[0], indent=2))
elif isinstance(data, dict):
    print(f"Number of keys: {len(data)}")
    print(f"Keys: {list(data.keys())}")
    print("\nData preview:")
    print(json.dumps(data, indent=2)[:1000])  # First 1000 chars

# Convert to DataFrame if possible
try:
    if isinstance(data, list) and data and isinstance(data[0], dict):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)
    
    print(f"\nDataFrame shape: {df.shape}")
    print("\nFirst row:")
    print(df.iloc[0] if not df.empty else "DataFrame is empty")
    
    # Save to CSV
    df.to_csv('output_json.csv', index=False)
    print("\nData saved to output_json.csv")
except Exception as e:
    print(f"\nCould not convert to DataFrame: {e}")

