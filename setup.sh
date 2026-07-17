#!/bin/bash
set -e

# ── Conda environment ──────────────────────────────────────────────────────────
if conda env list | awk '{print $1}' | grep -qx "timewarp"; then
  echo "Conda environment 'timewarp' already exists, skipping creation."
else
  echo "Creating conda environment from environment.yml..."
  conda env create -f environment.yml
fi
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate timewarp

# ── Playwright browser install ──────────────────────────────────────────────
echo "Installing Playwright browsers..."
python -m playwright install

# ── Webshop setup ──────────────────────────────────────────────────────────────
# The webshop server and indexer only ever read the *_1000.json files
# (web_agent_site/utils.py); use "-d all" only if you edit utils.py to point at
# the full dataset.
echo "Running webshop setup..."
cd env/webshop
bash setup.sh -d small

# ── Wiki setup ─────────────────────────────────────────────────────────────────
cd ../wiki
HF_BASE="https://huggingface.co/datasets/sparklabutah/timewarp-env-data/resolve/main"

if [ ! -f wiki_index.pkl ]; then
  echo "Downloading wiki_index.pkl..."
  curl -L --fail --progress-bar -o wiki_index.pkl.tmp "$HF_BASE/wiki_index.pkl"
  mv wiki_index.pkl.tmp wiki_index.pkl
else
  echo "wiki_index.pkl already exists, skipping download."
fi

# ── News setup ─────────────────────────────────────────────────────────────────
cd ../news
if [ ! -f news_index.pkl ]; then
  echo "Downloading news_index.pkl..."
  curl -L --fail --progress-bar -o news_index.pkl.tmp "$HF_BASE/news_index.pkl"
  mv news_index.pkl.tmp news_index.pkl
else
  echo "news_index.pkl already exists, skipping download."
fi

cd ../..

echo "Setup complete."
