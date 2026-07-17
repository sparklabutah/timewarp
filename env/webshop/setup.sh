#!/bin/bash
set -euo pipefail

# Displays information on how to use script
helpFunction()
{
  echo "Usage: $0 [-d small|all]"
  echo -e "\t-d small|all - Specify whether to download entire dataset (all) or just 1000 (small)"
  exit 1 # Exit script after printing help
}

# Get values of command line flags
while getopts d: flag
do
  case "${flag}" in
    d) data=${OPTARG};;
  esac
done

if [ -z "${data:-}" ]; then
  echo "[ERROR]: Missing -d flag"
  helpFunction
fi

if [ "$data" != "small" ] && [ "$data" != "all" ]; then
  echo "[ERROR]: argument for -d flag not recognized"
  helpFunction
fi

# Install Environment Dependencies via `conda`
# (pyserini 1.3 bundles an Anserini fatjar compiled for Java 21)
conda install -y -c conda-forge openjdk=21

# Download dataset into `data` folder. The files are mirrored on Hugging Face;
# the original WebShop Google Drive links now require sign-in and can no longer
# be fetched anonymously (e.g. via gdown).
HF_BASE="https://huggingface.co/datasets/sparklabutah/timewarp-env-data/resolve/main/webshop"

download() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "$file already exists, skipping download."
  else
    echo "Downloading $file..."
    curl -L --fail --progress-bar -o "$file.tmp" "$HF_BASE/$file"
    mv "$file.tmp" "$file"
  fi
}

mkdir -p data
cd data
# The *_1000 files are always required: web_agent_site/utils.py and the search
# engine indexer read them by default. "-d all" additionally fetches the full
# dataset for users who edit utils.py to point at it.
download items_shuffle_1000.json # product scraped info
download items_ins_v2_1000.json  # product attributes
if [ "$data" == "all" ]; then
  download items_shuffle.json # full product scraped info
  download items_ins_v2.json  # full product attributes
fi
download items_human_ins.json # human-authored goal instructions
cd ..

# Download spaCy NLP model (goal.py loads en_core_web_sm)
python -m spacy download en_core_web_sm

# Build search engine index
cd search_engine
mkdir -p resources resources_100 resources_1k resources_100k
python convert_product_file_format.py # convert items.json => required doc format
mkdir -p indexes
./run_indexing.sh
cd ..
