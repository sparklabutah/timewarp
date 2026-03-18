# TimeWarp for BrowserGym

Hello, researcher! We provide instructions to set TimeWarp with [BrowserGym](https://github.com/ServiceNow/BrowserGym). 

## Setup

Run the following command to install `browsergym-timewarp`:

```sh
pip install browsergym-timewarp
python -c "import nltk; nltk.download('punkt_tab')"
```
Set the OpenAI API Key:

```sh
export OPENAI_API_KEY="your-key"  # For fuzzy evaluation
```

## Usage

```python
import gymnasium as gym
import browsergym.timewarp

env = gym.make("browsergym/timewarp.1")
obs, info = env.reset()

# Run your agent

env.close()
```

## Adding Tasks

1. Add to `src/browsergym/timewarp/data/test.raw.json`
2. Update `TASK_IDS` in `config.py`
3. Add to `metadata/timewarp.csv`

Sites: `["wiki"]`, `["webshop"]`, `["news"]`
Placeholders: `__WIKI__`, `__WEBSHOP__`, `__NEWS__`

## Citation

Don't forget to cite [BrowserGym](https://github.com/ServiceNow/BrowserGym):

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
