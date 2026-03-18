# Inferences on TimeWarp

Welcome, researcher! To benchmark your favorite model on TimeWarp, you need to (a) host a model locally or use an API key, (b) host multiple versions of the TimeWarp environment, and (c) run inferences. Alternatively, you can use our [multi-benchmark](multiBenchmark) that does all these for you.

Note: You need to set the OpenAI API key for the judge model, regardless of the web agent that you are testing.

## A. Hosting a Model Locally (using vLLM)

1. (Optional) Create a conda environment for hosting the model. This is optional but *strongly recommended.* If you don't have conda installed then please follow these instructions from [here](https://www.anaconda.com/docs/getting-started/anaconda/install).

```sh
conda create -n vllm python=3.10
conda activate vllm
```

2. Install `vLLM` by following the instructions from [here](https://github.com/vllm-project/vllm) or run the following command:

```sh
pip install vllm
```

3. You can use the [`startVLMmodel.sh`](startVLMmodel.sh) to host both LLMs and VLMs. Simply run the script using this command:

```sh
bash vlm/startVLMmodel.sh --port <port_number> --model <name_or_model_path>
```

## B. Hosting Environments

Running multiple environments (Wiki, News, Shop) can be tedious. Luckily the [`run_all_env.sh`](environment/run_all_env.sh) script takes care of this by (a) running multiple environments at sequential ports, and (b) configuring the URL variables. Run the following command and pass the version number (1-6) to run a particular version of all environments.

```sh
bash environment/run_all_env.sh <version_number>
```

To stop all running environments, use [`stop_all_ports.sh`](environment/stop_all_ports.sh) by running this command:

```sh
bash environment/stop_all_ports.sh
```

## C. Standard Benchmark (using BrowserGym and AgentLab)

Your models are hosted, environments are running. Time to run a benchmark. The easiest way to run a web agent is by using [AgentLab](https://github.com/ServiceNow/AgentLab).

1. Create a new conda environment and install AgentLab in editable mode:

```sh
git clone https://github.com/ServiceNow/AgentLab
cd AgentLab
pip install -e .
playwright install
```

2. You also need to set the root directory of your AgentLab experiments result and API keys used:

```sh
export AGENTLAB_EXP_ROOT=<root directory of experiment results>  # defaults to $HOME/agentlab_results
export OPENAI_API_KEY=<your openai api key> # if openai models are used
```

3. You can now run a benchmark script for a particular task category. The benchmark makes 3 runs over the whole test split of that category. The scripts are provided in [`singleBenchmark`](singleBenchmark/). Before running the script, set your own flags in [`src/agentlab/agents/generic_agent/agent_configs.py`](https://github.com/ServiceNow/AgentLab/blob/main/src/agentlab/agents/generic_agent/agent_configs.py) and use that name in the benchmark script that you will run. The TimeWarp agents use thinking, memory, and plan.

4. Set the number of parallel jobs in the benchmark script. For instance, if you have 8 threads use:

```python
study.run(n_jobs=8, parallel_backend="joblib")
```
We like to use `-2` here, which tells it to use all available cores minus 1.

5. Now run the benchmark script. Here's a sample command:

```sh
python singleBenchmark/benchmarkGeneralWiki.py \
  --port 9000 \
  --version v1 \
  --model LLaMA-Factory/saves/qwen3-4b-thinking/full/sft
```

## D. Multi-Benchmark

The [`multiBenchmark`](multiBenchmark) scripts can run benchmark scripts on multiple models across multiple versions of the environment. It automatically hosts the web environment and models.

⚠️ You still need to install and set the conda environments for AgentLab, Browsergym, Vllm, and TimeWarp. If you install the conda environments using a different name, then you need to change the names inside the benchmark scripts. The default conda environment names are `browsergym`, `agentlab`, `vllm`, and `timewarp`. ⚠️

### Quick Start

1. Set the OpenAI API Key for the judge model:

```sh
export OPENAI_API_KEY="sk-..."
```

2. Run [`multiBenchmark/_run_multi.sh`](multiBenchmark/_run_multi.sh):

```sh
bash multiBenchmark/_run_multi.sh \
    --models  "path/to/model1,path/to/model2,..." \
    --scripts "singleBenchmark/benchmarkGeneralWiki.py,..." \
    --versions "1,2,..."
```

### Script Usage

| Script | Role |
|---|---|
| [`_run_multi.sh`](multiBenchmark/_run_multi.sh) | Entry point — validates `OPENAI_API_KEY`, parses args, delegates. |
| [`run_models.sh`](multiBenchmark/run_models.sh) | Loops over models, calls `run_with_vlm.sh` for each. |
| [`run_with_vlm.sh`](multiBenchmark/run_with_vlm.sh) | Starts a VLM server, runs all benchmark scripts, stops the server. |
| [`run_versions.sh`](multiBenchmark/run_versions.sh) | Runs a single benchmark script across the selected TimeWarp versions. |


## Citation

Don't forget to cite [BrowserGym](https://github.com/ServiceNow/BrowserGym), [AgentLab](https://github.com/ServiceNow/AgentLab), and [vLLM](https://github.com/vllm-project/vllm) for providing their amazing repos.

### BrowserGym and AgentLab

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

### vLLM

```bibtex
@inproceedings{kwon2023efficient,
  title={Efficient Memory Management for Large Language Model Serving with PagedAttention},
  author={Woosuk Kwon and Zhuohan Li and Siyuan Zhuang and Ying Sheng and Lianmin Zheng and Cody Hao Yu and Joseph E. Gonzalez and Hao Zhang and Ion Stoica},
  booktitle={Proceedings of the ACM SIGOPS 29th Symposium on Operating Systems Principles},
  year={2023}
}
```




