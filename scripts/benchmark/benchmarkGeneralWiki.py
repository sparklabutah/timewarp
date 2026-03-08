from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from agentlab.experiments.study import make_study
from browsergym.experiments.benchmark.configs import DEFAULT_BENCHMARKS

from agentlab.agents.generic_agent import AGENT_LLAMA3_70B
from agentlab.agents.generic_agent.generic_agent import GenericAgentArgs
from agentlab.agents.generic_agent.generic_agent_with_training import GenericAgentWithTrainingArgs
from agentlab.llm.chat_api import SelfHostedModelArgs

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run Qwen Thinking benchmark on TimeWarp")
parser.add_argument("--port", type=int, default=8000, help="Port number for vLLM API (default: 8000)")
parser.add_argument("--version", type=str, required=True, help="Version string for results directory (e.g., '1', '2', 'v1.0')")
parser.add_argument("--model", type=str, required=True, help="Model name/path (e.g., '/path/to/model' or 'LLaMA-Factory/saves/qwen3-4b-thinking/full/sft')")
args = parser.parse_args()

# Set environment variables for vLLM connection
# For local vLLM servers, the API key can be any non-empty string
os.environ["VLLM_API_KEY"] = "EMPTY"
os.environ["VLLM_API_URL"] = f"http://localhost:{args.port}/v1"

# Set TimeWarp environment variables if not already set
# Default to localhost ports (adjust if your TimeWarp instance uses different ports)

print(f"TimeWarp URLs:")
print(f"  TW_WIKI: {os.environ.get('TW_WIKI', 'not set')}")
print(f"  TW_WEBSHOP: {os.environ.get('TW_WEBSHOP', 'not set')}")
print(f"  TW_NEWS: {os.environ.get('TW_NEWS', 'not set')}")
print(f"  TW_HOME: {os.environ.get('TW_HOME', 'not set')}")

# Define a vLLM-hosted Qwen Thinking backend. Update host/port via env vars as needed.
qwen_thinking_vllm = SelfHostedModelArgs(
    model_name=args.model,
    max_total_tokens=65_000, # Change this based on the model that you are using
    max_input_tokens=65_000 - 8192,
    max_new_tokens=8192,  # Increased for thinking model to allow full reasoning output
    backend="vllm",
    temperature=0.01,
    n_retry_server=1,
)

# Reuse the stock GenericAgent prompt flags that work well for 70B-class models.
# The TimeWarp benchmark will automatically set the correct action subset (includes send_msg_to_user)
flags_70b_custom = AGENT_LLAMA3_70B.flags.copy()
flags_70b_custom.obs.use_error_logs = True 

# Get TimeWarp URLs from environment variables
tw_wiki = os.environ.get('TW_WIKI', 'localhost:5000')
tw_webshop = os.environ.get('TW_WEBSHOP', 'localhost:5002')
tw_news = os.environ.get('TW_NEWS', 'localhost:5001')
tw_home = os.environ.get('TW_HOME', 'localhost:5003')

flags_70b_custom.extra_instructions = f"""
IMPORTANT: You must only navigate to URLs within the TimeWarp environment. 
Do NOT navigate to external websites.
Only use the URLs provided in the TimeWarp environment.
WIKI URL: {tw_wiki}
NEWS URL: {tw_news}
SHOP URL: {tw_webshop}
For instance, goto("{tw_wiki}/") to navigate to WIKI. If you need to access Wikipedia content, use the local TimeWarp wiki instance instead.
Strictly follows the instructions provided in the task description.
You MUST output EXACTLY ONE action per response. Do NOT attempt multiple actions at once.
CRITICAL: Output the <action> tag ONLY ONCE, at the end of your response, OUTSIDE of any <think> tags.
Do NOT include <action> tags inside your reasoning section.
"""

generic_agent_args = GenericAgentWithTrainingArgs(
    chat_model_args=qwen_thinking_vllm,
    flags=flags_70b_custom,
)

timewarp_benchmark = DEFAULT_BENCHMARKS["timewarp"](n_repeats=3)
test_benchmark = timewarp_benchmark.subset_from_split("test")

test_benchmark.env_args_list = test_benchmark.env_args_list[0:93]
print(f"Running on task: {test_benchmark.env_args_list[0].task_name}")

# Create study with Qwen Thinking 4B model
study = make_study(
    benchmark=test_benchmark,
    agent_args=[generic_agent_args],
    comment="Qwen3-4B-Thinking on TimeWarp test split (joblib backend)",
)
# Extract model name for results directory (use last component of path)
model_name_for_dir = Path(args.model).name if "/" in args.model or "\\" in args.model else args.model
study.dir = Path(f"results/{model_name_for_dir}/{args.version}_wikiTest")  # Separate directory to avoid mixing with other results

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    
    # Note: joblib uses multiprocessing, which automatically inherits environment variables
    # No need for explicit environment variable setup like with Ray
    
    # Run study with joblib backend
    study.run(n_jobs=8, parallel_backend="joblib")

