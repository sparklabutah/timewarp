import torch
import pandas as pd

data = torch.load('data/webarena_lite_sft.pt')
print(f"Loaded type: {type(data)}")

if torch.is_tensor(data):
    df = pd.DataFrame(data.cpu().numpy())
elif isinstance(data, list) and data:
    first = data[0]
    if torch.is_tensor(first):
        stacked = torch.stack([item.cpu() for item in data])
        df = pd.DataFrame(stacked.numpy())
    elif isinstance(first, dict):
        df = pd.DataFrame(data)
    elif isinstance(first, (list, tuple)):
        df = pd.DataFrame(data)
    else:
        raise TypeError(f"Cannot convert list of {type(first)} to DataFrame")
elif isinstance(data, dict):
    if all(isinstance(v, (int, float, str, bool)) for v in data.values()):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame.from_dict(data, orient='index').transpose()
else:
    raise TypeError(f"Unsupported data type: {type(data)}")

print("First row:")
print(df.iloc[0] if not df.empty else "DataFrame is empty")
df.to_csv('output.csv', index=False)
