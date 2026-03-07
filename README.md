<h1 align="center">
  ⏳&nbsp;TimeWarp
</h1>

<p align="center">
A multi-environment web simulation framework featuring themed versions of Wiki, News, and Webshop environments.
</p>

---

## Table of Contents

- [Installation](#-installation)
  - [Conda Environment](#conda-environment)
  - [Environment Variables](#environment-variables)
- [Running Environments](#-running-environments)
  - [Start All](#start-all)
  - [Stop All](#stop-all)
- [Environment URLs](#-environment-urls)
- [Usage in Python](#-usage-in-python)
- [Verification](#-verification)

---

## 📦 Installation

### Conda Environment

Create and activate the conda environment:

```sh
conda env create -f environment.yml
conda activate timewarp
```

### Environment Variables

TimeWarp uses a `.env` file to configure service URLs. Create a `.env` file in the project root:

```sh
# Wiki URLs
WIKI1=http://localhost:5001
WIKI2=http://localhost:5002
WIKI3=http://localhost:5003
WIKI4=http://localhost:5004
WIKI5=http://localhost:5005
WIKI6=http://localhost:5006

# News URLs
NEWS1=http://localhost:5007
NEWS2=http://localhost:5008

# Webshop URLs
WEBSHOP1=http://localhost:5009
WEBSHOP2=http://localhost:5010
```

**Format rules:**

- `KEY=VALUE` — no spaces around `=`
- No quotes needed (unless the value itself contains spaces)
- One variable per line
- Comments start with `#`

Install `python-dotenv` if not already present:

```sh
pip install python-dotenv
```

Or install from the individual requirements files:

```sh
pip install -r env/wiki/requirements.txt
pip install -r env/news/requirements.txt
pip install -r env/webshop/requirements.txt
```

---

## 🚀 Running Environments

### Start All

Launch all environments (Wiki, News, Webshop) with a single script. A version number (1–6) selects the theme:

```sh
# Start all environments with theme version 1 (default)
./run_all_env.sh

# Start with a specific version
./run_all_env.sh 3

# Start and block the terminal (useful for foreground monitoring)
./run_all_env.sh 1 --wait
```

Ports are assigned automatically starting from 5000. On startup, the following environment variables are exported:

| Variable | Default | Description |
|----------|---------|-------------|
| `TW_WIKI` | `http://localhost:<port>` | Wiki environment URL |
| `TW_NEWS` | `http://localhost:<port>` | News environment URL |
| `TW_WEBSHOP` | `http://localhost:<port>/abc` | Webshop environment URL |

### Stop All

```sh
# Stop all tunnels and servers (default)
./stop_all_ports.sh

# Stop only the servers
./stop_all_ports.sh --servers

# Stop only tunnels (keep servers running)
./stop_all_ports.sh --tunnels-only
```

---

## 🌐 Environment URLs

Each environment supports 6 themes (versions 1–6), started via the `-N` flag:

| Environment | App | Port Range |
|-------------|-----|------------|
| Wiki | `env/wiki/wiki_app.py` | 5000:5005 |
| News | `env/news/news_app.py` | 5006:5011 |
| Webshop | `env/webshop/web_agent_site/app.py` | 5012:5017 |

---

## 🐍 Usage in Python

Load `.env` variables in any Python file:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Access a variable (with optional default)
wiki_url = os.getenv('WIKI1', 'http://localhost:5001')
print(wiki_url)  # http://localhost:5001
```

Example — connect to a theme-specific environment:

```python
import os
from dotenv import load_dotenv

load_dotenv()

wiki1 = os.getenv('WIKI1')
if wiki1:
    print(f"Connecting to {wiki1}")
else:
    print("WIKI1 not found in .env file")
```

---

## ✅ Verification

After creating your `.env` file, verify it loads correctly:

```sh
python env/example_env_usage.py
```

This should print the URLs defined in your `.env` file.

