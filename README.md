<h1 align="center">
  ⏳&nbsp;TimeWarp: Evaluating Web Agents by Revisiting the Past
</h1>

<div align="center">
  
[![project](https://img.shields.io/badge/Project%20Page-4285F4?style=flat&logo=homeassistant&logoColor=white&color=006A4E&labelColor=gray)](https://timewarp-web.github.io)
[![arXiv](https://img.shields.io/badge/arXiv-2603.04949-b31b1b.svg?logo=arxiv&labelColor=FFFFFF&logoColor=b31b1b)](https://arxiv.org/abs/2603.04949)
[![code](https://img.shields.io/badge/GitHub-sparklabutah/timewarp-blue?logo=GitHub&labelColor=black)](https://github.com/sparklabutah/timewarp)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20_Dataset-sparklabutah/timewarp-ffc107?color=ffc107&logoColor=white)](https://huggingface.co/datasets/sparklabutah/timewarp)
[![license](https://img.shields.io/badge/License-MIT-purple.svg)]()

</div>

tldr. TimeWarp is a benchmark for evaluating the robustness of agents to temporal changes in web UI. TimeWarp consists of three web environments: Wiki, News, and Shop, each with six UI versions across different eras of the internet. The benchmark also includes TimeTraj, a method for scalably collecting trajectories via human-refined plans, and TimeWarp-BC, a variant of Behavior Cloning (BC) to train agents better via knowledge distillation on complex tasks that require memory and planning.

---

## Table of Contents

- [Installation](#-installation)
- [Running Environments](#-running-environments)
  - [Single Environment](#single-environment)
  - [Multiple Environments](#multiple-environments)
- [Create your Own Theme!](#-create-your-own-theme)
- [Running your Web Agent](#-running-your-web-agent)
- [Training your Web Agent](#️-training-your-web-agent)
- [Citation](#citation)

---



## 📦 Installation

Note: Ensure `conda` is installed on your system. If you don't have `conda` installed then please follow these instructions from [here](https://www.anaconda.com/docs/getting-started/anaconda/install).


Simply run [`setup.sh`](setup.sh) which will create a conda environment called `timewarp` and install the required dependencies:

```sh
bash setup.sh
```

---

## 🌐 Running Environments

### Single Environment

Run the following commands to start a single or multiple versions of the environment by passing the version number `[1-6]` or `all` argument:

```sh
bash env/wiki/start_wiki.sh [-1|-2|-3|-4|-5|-6|-all] # Wiki
bash env/news/start_news.sh [-1|-2|-3|-4|-5|-6|-all] # News
bash env/webshop/start_webshop.sh [-1|-2|-3|-4|-5|-6|-all] # Shop
```

Example Usage:
```sh
bash env/webshop/start_webshop.sh -1
```

### Multiple Environments

Helper scripts for running multiple environments are provided in [`scripts/environment`](scripts/environment/), with [additional instructions](scripts/README.md). Sample usage is given below:

```sh
# Start all environments with theme version 1 (default)
./run_all_env.sh

# Start with a specific version
./run_all_env.sh 3

# Start and block the terminal (useful for foreground monitoring)
./run_all_env.sh 1 --wait

# Stop all tunnels and servers (default)
./stop_all_ports.sh
```

Ports are assigned automatically starting from 5000. On startup, the following environment variables are exported:

| Variable | Default | Description |
|----------|---------|-------------|
| `TW_WIKI` | `http://localhost:<port>` | Wiki environment URL |
| `TW_NEWS` | `http://localhost:<port>` | News environment URL |
| `TW_WEBSHOP` | `http://localhost:<port>/abc` | Webshop environment URL |

---

## 🎨 Create your Own Theme!

Each environment loads its UI from a theme folder. To add a new theme, create a folder under the appropriate path:

| Environment | Theme directory |
|-------------|----------------|
| Wiki | `env/wiki/themes/<your-theme>/` |
| News | `env/news/themes/<your-theme>/` |
| Shop | `env/webshop/web_agent_site/themes/<your-theme>/` |

**Wiki & News** themes are flat directories. Drop in HTML templates and a stylesheet:

```
<your-theme>/
├── base.html
├── index.html
├── article.html
├── 404.html
├── style.css
└── script.js
```
News also expects `browse.html` and `search.html`. If you prefer, you can use `templates/` and `static/` subdirectories instead of the flat layout — the apps detect either structure automatically (Wiki only; News expects a flat layout).

**Shop** themes use a two-subfolder layout:

```
<your-theme>/
├── templates/   # search_page.html, results_page.html, item_page.html,
│                # description_page.html, features_page.html, attributes_page.html,
│                # review_page.html, done_page.html
└── static/      # style.css (and any images)
```

Once the folder is ready, register it by adding an entry to `num_to_theme` (and optionally `name_aliases`) inside `_parse_args` in the corresponding app file:

| Environment | App file |
|-------------|----------|
| Wiki | `env/wiki/wiki_app.py` |
| News | `env/news/news_app.py` |
| Shop | `env/webshop/web_agent_site/app.py` |

Then launch the environment with your theme name or its assigned number:

```sh
bash env/wiki/start_wiki.sh -<number>
# or
python env/wiki/wiki_app.py --<your-theme-name>
```

---

## 🤖 Running your Web Agent

To benchmark a model on TimeWarp you need three things running: a model, the environments, and a benchmark script.

**1. Host a model.** Use an API key (e.g. `OPENAI_API_KEY`) or serve a local model with `vllm`. The [`startVLMmodel.sh`](scripts/startVLMmodel.sh) script handles both LLMs and VLMs:

```sh
bash scripts/startVLMmodel.sh --port <port> --model <name_or_path>
```

**2. Start the environments.** Run all three environments at once with a single version flag:

```sh
bash scripts/environment/run_all_env.sh <version_number>   # e.g. 3
```

Stop everything when done:

```sh
bash scripts/environment/stop_all_ports.sh
```

**3. Run a benchmark.** The recommended way is [AgentLab](https://github.com/ServiceNow/AgentLab). After installing it and adding the [required TimeWarp lines](scripts/README.md), run a single benchmark script:

```sh
python scripts/singleBenchmark/benchmarkGeneralWiki.py \
  --port 9000 \
  --version v1 \
  --model <model_name_or_path>
```

To sweep across multiple models and environment versions automatically, use the multi-benchmark entry point:

```sh
bash scripts/multiBenchmark/_run_multi.sh \
  --models  "path/to/model1,path/to/model2" \
  --scripts "singleBenchmark/benchmarkGeneralWiki.py,..." \
  --versions "1,2,3"
```

See [`scripts/README.md`](scripts/README.md) for the full setup and AgentLab configuration details.

---

## 🏋️‍♂️ Training your Web Agent

TimeWarp agents are fine-tuned on teacher trajectories using [LlamaFactory](https://github.com/hiyouga/LlamaFactory). Multi-GPU training with DeepSpeed ZeRO-3 is recommended.

**1. Set up LlamaFactory.**

```sh
git clone --depth 1 https://github.com/hiyouga/LlamaFactory.git
cd LlamaFactory && pip install -e .
```

**2. Get training data.** Generate teacher trajectories or download our GPT-5 traces directly:

```sh
git clone https://huggingface.co/datasets/sparklabutah/TimeWarp-GPT5-Traces
```

Convert them to ShareGPT format using [`convert2sgptArgs.py`](llamafactory/helperScripts/convert2sgptArgs.py), then place the output JSON in `LlamaFactory/data/` and register it in `dataset_info.json`.

**3. Train.**

```sh
llamafactory-cli train examples/train_full/your_training_config.yaml
```

Example `.yaml` configs for both full fine-tuning and LoRA are provided in [`llamafactory/train_full`](llamafactory/train_full) and [`llamafactory/train_lora`](llamafactory/train_lora). See [`llamafactory/README.md`](llamafactory/readme.md) for the complete walkthrough.

---

## Citation

If you enjoyed using this repo, please consider citing our work:

```bibtex
@misc{timewarp2026,
      title={TimeWarp: Evaluating Web Agents by Revisiting the Past}, 
      author={Md Farhan Ishmam and Kenneth Marino},
      year={2026},
      eprint={2603.04949},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2603.04949}, 
  }
```
