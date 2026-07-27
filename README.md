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
- [How Tasks are Scored](#-how-tasks-are-scored)
- [Training your Web Agent](#️-training-your-web-agent)
- [Citation](#citation)

---

## 📦 Installation

⚠️ Ensure `conda` is installed on your system. If you don't have `conda` installed then please follow these instructions from [here](https://www.anaconda.com/docs/getting-started/anaconda/install). ⚠️


Simply run [`setup.sh`](setup.sh) which will create a conda environment called `timewarp` and install the required dependencies:

```sh
bash setup.sh
```

All environment data (including the [`env/webshop`](env/webshop/) product data, which the original webshop [repo](https://github.com/princeton-nlp/WebShop) hosted on Google Drive) is downloaded from the [timewarp-env-data](https://huggingface.co/datasets/sparklabutah/timewarp-env-data) Hugging Face dataset, so no Google Drive access or `gdown` is required.

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
## 📝 Running Tasks on Environment

You can use TimeWarp directly with [BrowserGym](https://github.com/ServiceNow/BrowserGym):

```python
import gymnasium as gym
import browsergym.timewarp

env = gym.make("browsergym/timewarp.1")
obs, info = env.reset()
# Run your agent
env.close()
```

Make sure the TimeWarp environments are running (see [Running Environments](#-running-environments)) and the following environment variables are set:

```sh
export TW_WIKI="http://localhost:5000"
export TW_WEBSHOP="http://localhost:5001"
export TW_NEWS="http://localhost:5002"
export OPENAI_API_KEY="your-key"  # For the default GPT judge; or set TW_JUDGE=gemma
                                  # for the open-source judge (see "How Tasks are Scored")
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

**3. Run a benchmark.** The recommended way is [AgentLab](https://github.com/ServiceNow/AgentLab). After installing it, run a single benchmark script:

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

## 📏 How Tasks are Scored

Tasks are scored by **deterministic verifiers** — no LLM in the loop, no API key,
no sampling variance. An agent's free-text answer is normalized (case, unicode,
markdown, punctuation, number formatting) and then checked against a per-task
reference spec. The design follows
[WebArena](https://github.com/web-arena-x/webarena) and
[WebArena-Verified](https://github.com/ServiceNow/BrowserGym/tree/main/browsergym/webarena_verified).

Each task declares its verifiers in `eval.eval_types`; several combine with AND.

| Verifier | Checks | Typical task |
|---|---|---|
| `string_match` | `must_include` / `must_exclude` / `exact_match`, matched on word boundaries so `"10"` never matches `"100"` | named entities, titles, years, yes/no |
| `number_match` | the expected number appears, whatever its formatting (`7,000,000`, `7 million`, `thirteen`) | counts, prices, populations |
| `list_match` | every item of an enumeration appears, optionally in order | "list all countries, alphabetically" |
| `llm_judge` | the GPT judge, or an open-source alternate (see below) | the residual tasks with no objectively checkable answer |

Entries support `" |OR| "` alternatives and `^regex$` leaves, and
`"scope": "first_sentence"` restricts matching to the leading sentence — which is
how a yes/no verdict is read without a justification tail leaking the opposite
token.

### Running the scorers

**During a benchmark run** scoring is automatic: each task is routed to the
verifiers in its `eval.eval_types`, and the reward comes back on `env.step`. No
extra flags. A deterministic task needs nothing; only a task still on `llm_judge`
needs a judge configured — `OPENAI_API_KEY` for the default GPT judge, or a
served open-source model selected with `TW_JUDGE` (see
[Choosing the LLM judge](#choosing-the-llm-judge)).

**Re-scoring recorded episodes** — score an AgentLab study directory (or a JSONL
of `{task_id, answer}` via `--answers`) after the fact with
[`rescore_compare.py`](scripts/analysis/rescore_compare.py):

```sh
# Deterministic verifiers only — no API key, no cost, no sampling variance
python scripts/analysis/rescore_compare.py <study_dir>

# Deterministic + GPT judge (default), and report where the two disagree
export OPENAI_API_KEY="your-key"
python scripts/analysis/rescore_compare.py <study_dir> --judge

# Deterministic + open-source judge (serve it first; see below)
export TW_JUDGE=gemma
python scripts/analysis/rescore_compare.py <study_dir> --judge
# ...or pick the judge inline without the env var:
python scripts/analysis/rescore_compare.py <study_dir> --judge --judge-model gemma
```

### Writing a deterministic verifier

Each task's spec lives under `eval.reference_answers`; `eval.eval_types` lists
which verifiers run (multiple are AND-ed). Pick the **strictest** verifier that
still accepts every genuinely correct answer. Normalization already handles case,
unicode/accents, markdown emphasis, surrounding quotes/punctuation, and
whitespace — you only spell out real wording or number-format alternatives.

**`string_match`** — named entities, titles, years, yes/no. The default.

```json
{
  "eval_types": ["string_match"],
  "reference_answers": {
    "must_include": ["hdmi"],
    "must_exclude": ["usb charger"],
    "scope": "first_sentence"
  }
}
```

| Key | Meaning |
|---|---|
| `must_include` | Every entry must appear, matched on word boundaries (`"10"` never matches `"100"`; `"no"` never matches `"north"`). |
| `must_exclude` | No entry may appear. Reserve for tokens that **cannot** occur in any correct answer (e.g. a competing option, or `"both"`/`"neither"`). |
| `exact_match` | String or list; the whole normalized answer must equal one. Use only for bare-value answers — a verbose sentence fails it. |
| `scope` | `"full"` (default) or `"first_sentence"`. |

**`number_match`** — counts, prices, measurements. Parses every number out of
the answer (`1,234.56`, `$9.99`, `57.7 million`, `13th`, spelled-out `thirteen`)
and requires the expected value among them. Comparison is **exact unless you give
a tolerance**.

```json
{
  "eval_types": ["number_match"],
  "reference_answers": {
    "number_match": {"value": 7000000, "rel_tolerance": 0.1}
  }
}
```

| Key | Meaning |
|---|---|
| `value` / `values` | A required number, or a list of numbers that must all appear. |
| `abs_tolerance` | Absolute slack (e.g. `0.01` for currency). |
| `rel_tolerance` | Relative slack — only for a gold that is itself hedged ("around 7 million"). |
| `scope` | `"full"` (default) or `"first_sentence"`. |

**`list_match`** — enumerations. Each item is a list of interchangeable
spellings; all items must appear. Set `ordered: true` **only when the task itself
demands an order** ("in alphabetical order", a ranking, a navigation path).

```json
{
  "eval_types": ["list_match"],
  "reference_answers": {
    "list_match": {
      "items": [["germany"], ["italy"], ["luxembourg |OR| luxemburg"]],
      "ordered": true,
      "forbidden": []
    }
  }
}
```

| Key | Meaning |
|---|---|
| `items` | List of items; each is a list of interchangeable spellings (a bare string is accepted). |
| `ordered` | If `true`, items' first occurrences must appear in the listed order. |
| `forbidden` | Entries that must not appear. |
| `scope` | `"full"` (default) or `"first_sentence"`. |

**Shared conventions.** Any entry may offer alternatives with `" |OR| "`
(`"kangaroos |OR| kangaroo"`); an entry written as `^...$` is a regex over the
normalized (scoped) text.

> **Common trap.** If the gold string (or a distractor) also appears in the
> task's `intent` — *"Which cable is longer, the HDMI cable or the USB charger
> cable?"* — a plain `must_include` on the full answer is compromised, because a
> wrong answer restates the question. Set `scope: "first_sentence"`,
> `must_include` the token unique to the **correct** option, and `must_exclude`
> the token unique to the **wrong** one.

The full authoring guide — verifier selection table, the complete set of traps,
confidence levels, and the required positive/negative test cases every spec must
ship — is in
[`scripts/annotation/GUIDELINES.md`](scripts/annotation/GUIDELINES.md).

### Choosing the LLM judge

The residual `llm_judge` tasks are graded by **GPT-5** by default (`OPENAI_API_KEY`
required). For a fully reproducible, cost-free alternative — and the open/closed
judge-agreement numbers reported in the paper — you can swap in an **open-source
judge (Gemma‑4 12B)** served locally through vLLM's OpenAI-compatible endpoint:

```sh
# 1. Serve the judge (any OpenAI-compatible server works; default port 8001)
bash scripts/startVLMmodel.sh --port 8001 --model google/gemma-4-12b-it

# 2. Point the harness at it — one env var flips every llm_judge task
export TW_JUDGE=gemma                       # alias for google/gemma-4-12b-it
export VLLM_API_URL=http://localhost:8001/v1  # only if not the default above
```

Selection is resolved in [`evaluators.py`](src/browsergym/timewarp/evaluators.py)
(`resolve_judge`): a GPT/o-series id goes to the OpenAI API, anything else is
treated as an open-weights model behind an OpenAI-compatible server. Precedence is
`TW_JUDGE` env var → a task's `eval.llm_model` → the GPT default. Override the
served id with `TW_JUDGE_MODEL`, the endpoint with `TW_JUDGE_BASE_URL`, and the key
with `TW_JUDGE_API_KEY` (defaults to the throwaway `EMPTY` vLLM accepts). To A/B
the two judges on recorded episodes:

```sh
python scripts/analysis/rescore_compare.py <study_dir> --judge --judge-model gpt-5
python scripts/analysis/rescore_compare.py <study_dir> --judge --judge-model gemma
```

Only tasks still on `llm_judge` need `OPENAI_API_KEY` (GPT judge) or a running
open-source server (Gemma judge). Verifier code lives in
[`normalization.py`](src/browsergym/timewarp/normalization.py) and
[`evaluators.py`](src/browsergym/timewarp/evaluators.py), with tests in
[`test_evaluators.py`](src/tests/timewarp/test_evaluators.py):

```sh
pytest src/tests/timewarp/test_evaluators.py
```

The per-task specs were annotated and adversarially verified by the pipeline in
[`scripts/annotation/`](scripts/annotation/), which also documents how to add or
retune a verifier and how to spot-check a gold answer against environment
content.

---

## 🏋️ Training your Web Agent

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

Don't forget to cite all the repos that have helped us!

### Browsergym and AgentLab
```bibtex
@article{
    chezelles2025browsergym,
    title={The BrowserGym Ecosystem for Web Agent Research},
    author={Thibault Le Sellier de Chezelles and Maxime Gasse and Alexandre Lacoste and Massimo Caccia and Alexandre Drouin and L{\'e}o Boisvert and Megh Thakkar and Tom Marty and Rim Assouel and Sahar Omidi Shayegan and Lawrence Keunho Jang and Xing Han L{\`u} and Ori Yoran and Dehan Kong and Frank F. Xu and Siva Reddy and Graham Neubig and Quentin Cappart and Russ Salakhutdinov and Nicolas Chapados},
    journal={Transactions on Machine Learning Research},
    issn={2835-8856},
    year={2025},
    url={https://openreview.net/forum?id=5298fKGmv3},
    note={Expert Certification}
}
```

### WebShop
```bibtex
@inproceedings{yao2022webshop,
  bibtex_show = {true},
  title = {WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents},
  author = {Yao, Shunyu and Chen, Howard and Yang, John and Narasimhan, Karthik},
  booktitle = {ArXiv},
  year = {preprint},
  html = {https://arxiv.org/abs/2207.01206},
  tag = {NLP}
}
```
If you enjoyed using this repo, also consider citing us! 😊

### TimeWarp
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
