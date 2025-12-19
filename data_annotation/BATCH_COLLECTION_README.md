# Batch Data Collection Guide

## Overview

The batch collection script automates the process of collecting multiple trajectories for training data. URLs are automatically loaded from the `.env` file based on environment and variant.

## Prerequisites

Make sure your `.env` file is set up with the correct URLs:

```bash
# .env file example
WIKI1=http://localhost:5001
WIKI2=http://localhost:5002
NEWS1=http://localhost:5007
SHOP1=http://localhost:5009
HOME1=http://localhost:5011
```

## Usage

```bash
./data_annotation/collect_batch.sh <env> <variant>
```

### Parameters

1. **env**: Environment type - one of:
   - `wiki` (39 iterations) → Uses `WIKI{variant}` from .env
   - `news` (32 iterations) → Uses `NEWS{variant}` from .env
   - `webshop` (45 iterations) → Uses `SHOP{variant}` from .env
   - `homepage` (5 iterations) → Uses `HOME{variant}` from .env
2. **variant**: Theme/variant number (1-6) or `all`
   - `1-6`: Collect all traces for a single theme
   - `all`: Collect traces sequentially across all 6 themes

### How URLs are Loaded

The script automatically constructs the environment variable name:

- `wiki 1` → `WIKI1`
- `news 3` → `NEWS3`
- `webshop 2` → `SHOP2`
- `homepage 4` → `HOME4`

### Examples

#### Single Theme Collection

```bash
# Collect 39 wiki trajectories for theme 1 (uses WIKI1 from .env)
./data_annotation/collect_batch.sh wiki 1

# Collect 32 news trajectories for theme 3 (uses NEWS3 from .env)
./data_annotation/collect_batch.sh news 3

# Collect 45 webshop trajectories for theme 2 (uses SHOP2 from .env)
./data_annotation/collect_batch.sh webshop 2

# Collect 5 homepage trajectories for theme 1 (uses HOME1 from .env)
./data_annotation/collect_batch.sh homepage 1
```

#### All Themes Collection (Sequential)

```bash
# Collect wiki traces across all 6 themes sequentially
./data_annotation/collect_batch.sh wiki all

# This will collect:
#   Trace 1: theme1 → theme2 → theme3 → theme4 → theme5 → theme6
#   Trace 2: theme1 → theme2 → theme3 → theme4 → theme5 → theme6
#   ... (39 times for wiki)
```

### Collection Order with "all"

When using `all`, the script collects traces in this order:

```
Trace ID 1:
  - wiki/theme_1/1_trace.zip
  - wiki/theme_2/1_trace.zip
  - wiki/theme_3/1_trace.zip
  - wiki/theme_4/1_trace.zip
  - wiki/theme_5/1_trace.zip
  - wiki/theme_6/1_trace.zip

Trace ID 2:
  - wiki/theme_1/2_trace.zip
  - wiki/theme_2/2_trace.zip
  - wiki/theme_3/2_trace.zip
  - wiki/theme_4/2_trace.zip
  - wiki/theme_5/2_trace.zip
  - wiki/theme_6/2_trace.zip

... and so on
```

This ensures you get diverse data across all themes before repeating the same theme.

## Output Structure

Files are saved in the following structure:

```
trajectories/
├── wiki/
│   ├── theme_1/
│   │   ├── 1_trace.zip
│   │   ├── 1_exit_message.txt
│   │   ├── 2_trace.zip
│   │   ├── 2_exit_message.txt
│   │   └── ...
│   ├── theme_2/
│   └── ...
├── news/
│   ├── theme_1/
│   └── ...
├── webshop/
│   ├── theme_1/
│   └── ...
└── homepage/
    ├── theme_1/
    └── ...
```

## Workflow for Each Iteration

1. **Browser opens** automatically
2. **Perform your task** in the browser (click, type, navigate)
3. **Close the browser window** when done
4. **Enter exit message** in the terminal (your final answer)
5. **Press ENTER** to continue to next iteration

## Features

- ✅ **Auto-creates directories** for organized storage
- ✅ **Skips existing files** - won't overwrite completed iterations
- ✅ **Progress tracking** - shows iteration X of Y
- ✅ **Error handling** - stops if files aren't created properly
- ✅ **Resume support** - can restart script and it will skip completed iterations

## Tips

1. **Start small**: Test with `homepage` (5 iterations) first
2. **Take breaks**: The script will wait for you between iterations
3. **Check progress**: Files are saved immediately after each iteration
4. **Resume anytime**: If interrupted, just run the same command again

## Processing Collected Data

After collection, process the traces into training data:

```bash
python data_annotation/process_traces.py \
  --input trajectories/wiki/theme_1/ \
  --task "Your task description" \
  --observation-type html \
  --output training_data_wiki_theme1.json
```

Or generate all observation types:

```bash
python data_annotation/process_traces.py \
  --input trajectories/wiki/theme_1/ \
  --task "Your task description" \
  --generate-all \
  --output training_data_wiki_theme1
```

This will create:

- `training_data_wiki_theme1_html.json`
- `training_data_wiki_theme1_axtree.json`
- `training_data_wiki_theme1_both.json`
