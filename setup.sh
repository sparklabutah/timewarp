#!/bin/bash
set -e

# ── Conda environment ──────────────────────────────────────────────────────────
echo "Creating conda environment from environment.yml..."
conda env create -f environment.yml || echo "Environment already exists, skipping creation."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate timewarp

# ── Webshop setup ──────────────────────────────────────────────────────────────
echo "Running webshop setup..."
cd env/webshop
bash setup.sh -d all

# ── Wiki setup ─────────────────────────────────────────────────────────────────
cd ../wiki
HF_BASE="https://huggingface.co/datasets/sparklabutah/timewarp-env-data/resolve/main"

if [ ! -f wiki_index.pkl ]; then
  echo "Downloading wiki_index.pkl..."
  curl -L --progress-bar -o wiki_index.pkl "$HF_BASE/wiki_index.pkl"
else
  echo "wiki_index.pkl already exists, skipping download."
fi

# ── News setup ─────────────────────────────────────────────────────────────────
cd ../news
if [ ! -f news_index.pkl ]; then
  echo "Downloading news_index.pkl..."
  curl -L --progress-bar -o news_index.pkl "$HF_BASE/news_index.pkl"
else
  echo "news_index.pkl already exists, skipping download."
fi

cd ../..

echo "Setup complete."
