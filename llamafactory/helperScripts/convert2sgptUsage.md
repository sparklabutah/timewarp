# Usage Examples for convert2sgptArgs.py

## Basic Usage (action only - default)
```bash
python convert2sgptArgs.py input_folder/ --output output.json
```

## With All Tags (think, plan, memory)
```bash
python convert2sgptArgs.py input_folder/ --output output.json --think --plan --memory
```

## Individual Tag Examples

### Include thinking/reasoning sections
```bash
python convert2sgptArgs.py input_folder/ --output output.json --think
```

### Include plan and step sections
```bash
python convert2sgptArgs.py input_folder/ --output output.json --plan
```

### Include memory sections
```bash
python convert2sgptArgs.py input_folder/ --output output.json --memory
```

### Combine multiple tags
```bash
python convert2sgptArgs.py input_folder/ --output output.json --think --plan
python convert2sgptArgs.py input_folder/ --output output.json --think --memory
python convert2sgptArgs.py input_folder/ --output output.json --plan --memory
```

## Subsampling Trajectories with Probability `p`

You can randomly subsample trajectories (task folders) using the `--p` argument (default `1.0` means use all trajectories):

```bash
# Use 80% of trajectories on average
python convert2sgptArgs.py input_folder/ --output output.json --p 0.8

# Combine with tag options
python convert2sgptArgs.py input_folder/ --output output.json --think --plan --memory --p 0.5
```

The value of `--p` must be between `0` and `1`. Each trajectory is independently included with probability `p`.

## Sampling and Dropout

You can duplicate trajectories using the `--sampling` argument (default `1` means no duplication), and then apply dropout with `--p`:

```bash
# Sample each trajectory 6 times, then apply dropout with p=0.5
python convert2sgptArgs.py input_folder/ --output output.json --sampling 6 --p 0.5

# Combine with tag options
python convert2sgptArgs.py input_folder/ --output output.json --think --plan --sampling 3 --p 0.8
```

**Order of operations:**
1. First, each trajectory is duplicated `sampling` times (e.g., if `--sampling 6`, each trajectory becomes 6 copies)
2. Then, dropout `p` is applied to each duplicate independently (each copy has probability `p` of being kept)

**Example:** With 1 trajectory, `--sampling 6`, and `--p 0.5`:
- First: 6 copies are created
- Then: Each copy has a 50% chance of being kept
- Expected result: ~3 copies in the output

The value of `--sampling` must be `>= 1`.

## What Each Tag Does

- `--think`: Includes `<think>` tags containing the agent's reasoning/thinking
- `--plan`: Includes `<plan>` and `<step>` tags containing planning information
- `--memory`: Includes `<memory>` tags containing memory updates
- **Note**: `<action>` tags are ALWAYS included regardless of flags

## Example Output Structure

With all flags (`--think --plan --memory`), the output will contain:
```json
{
  "system": "System prompt text...",
  "conversations": [
    {
      "from": "human",
      "value": "User prompt text..."
    },
    {
      "from": "gpt",
      "value": "<think>\nThinking content...\n</think>\n\n<plan>\nPlan content...\n</plan>\n\n<step>Step content...</step>\n\n<memory>\nMemory content...\n</memory>\n\n<action>\nAction content...\n</action>"
    }
  ]
}
```plan to include