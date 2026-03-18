# Fine-tuning Models using LlamaFactory

Welcome, fellow researcher! We will guide you how to fine-tune your web agent on TimeWarp using [LlamaFactory](https://github.com/hiyouga/LlamaFactory). We recommend using [DeepSpeed ZeRO-3](https://www.deepspeed.ai/2021/03/07/zero3-offload.html) for multi-GPU training.

## Getting Started

### A. Setting up LlamaFactory

1. (Optional) Create a conda environment for training. This is optional but *strongly recommended.* If you don't have conda installed then please follow these instructions from [here](https://www.anaconda.com/docs/getting-started/anaconda/install).

```sh
conda create -n timewarpTraining python=3.10
conda activate timewarpTraining
```

2. Clone the official LlamaFactory repo from [here](https://github.com/hiyouga/LlamaFactory) and install the required dependencies. The commands are given here:
```sh
git clone --depth 1 https://github.com/hiyouga/LlamaFactory.git
cd LlamaFactory
pip install -e .
pip install -r requirements/metrics.txt
```

3. (Optional) If you are training on multiple GPUs, install DeepSpeed:
```sh
pip install -r requirements/deepspeed.txt
```

### B. Generating Training Data

TimeWarp models are trained on the trajectories of a teacher web agent. The generated trajectory is converted to the `ShareGPT` format for training.

1. Collect teacher trajectories following the instructions in [`collectTeacherTraj/README.MD`](../collectTeacherTraj/README.MD). Optionally, use the teacher trajectories that we generated from the GPT agent by downloading them from [`huggingface/sparklabutah/TimeWarp-GPT5-Traces`](https://huggingface.co/datasets/sparklabutah/TimeWarp-GPT5-Traces).

```sh
git clone https://huggingface.co/datasets/sparklabutah/TimeWarp-GPT5-Traces
```

2. Run the [`convert2sgptArgs.py`](helperScripts/convert2sgptArgs.py) script to generate your desired training data in `ShareGPT` format. Instructions on using this script have been provided in [`convert2sgptUsage.md`](helperScripts/convert2sgptUsage.md). We also provide the data for training on the action, thinking, memory, and planning tokens, with the AXT on the all TimeWarp tasks and versions using the GPT-5 model: [`timewarpTracesSingle.json`](timewarpTracesSingle.json).

3. Once the training data is generated, place it in [`LlamaFactory/data`](https://github.com/hiyouga/LlamaFactory/tree/main/data).

4. Update the [`dataset_info.json`](https://github.com/hiyouga/LlamaFactory/blob/main/data/dataset_info.json) file with the dataset metadata. We also provide an example [`dataset_info.json`](dataset_info.json) file.

### C. Train your Agent!

Training a web agent is simple. 

1. Update the `.yaml` files in [`LlamaFactory/examples/train_full`](https://github.com/hiyouga/LlamaFactory/tree/main/examples/train_full) and [`LlamaFactory/examples/train_lora`](https://github.com/hiyouga/LlamaFactory/tree/main/examples/train_lora) for full fine-tuning and LoRA fine-tuning, respectively. Example files are provided in [`train_full`](train_full) and [`train_lora`](train_lora).

2. Train your agent by running the command (make sure you are in the LlamaFactory directory):
```sh
llamafactory-cli train examples/train_full/your_training_config.yaml
```

Great job, your agent is now being trained! You will most likely encounter tons of technical hurdles while following these steps. Setting the environment and training for the first time can be the hardest step. Feel free to reach out to the authors for any kinda difficulty! 

## Citation

Don't forget to cite [LlamaFactory](https://github.com/hiyouga/LlamaFactory) for providing their amazing repo.

```bibtex
@inproceedings{zheng2024llamafactory,
  title={LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models},
  author={Yaowei Zheng and Richong Zhang and Junhao Zhang and Yanhan Ye and Zheyan Luo and Zhangchi Feng and Yongqiang Ma},
  booktitle={Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 3: System Demonstrations)},
  address={Bangkok, Thailand},
  publisher={Association for Computational Linguistics},
  year={2024},
  url={http://arxiv.org/abs/2403.13372}
}
```