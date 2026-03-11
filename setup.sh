#!/bin/bash
set -e

# ── Conda environment ──────────────────────────────────────────────────────────
echo "Creating conda environment from environment.yml..."
conda env create -f environment.yml || echo "Environment already exists, skipping creation."
conda activate timewarp

# ── Webshop setup ──────────────────────────────────────────────────────────────
echo "Running webshop setup..."
bash env/webshop/setup.sh "$@"

# ── Download index files ───────────────────────────────────────────────────────
HF_BASE="https://huggingface.co/datasets/sparklabutah/timewarp-env-data/resolve/main"

echo "Downloading wiki_index.pkl..."
mkdir -p env/wiki
curl -L --progress-bar -o env/wiki/wiki_index.pkl "$HF_BASE/wiki_index.pkl"

echo "Downloading news_index.pkl..."
mkdir -p env/news
curl -L --progress-bar -o env/news/news_index.pkl "$HF_BASE/news_index.pkl"

echo "Setup complete."
