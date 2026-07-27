"""Compare deterministic verifier scores against the LLM judge on recorded episodes.

Deterministic verifiers are strictly stricter than the judge in places, so
before swapping them in it is worth seeing exactly where the two disagree and
adjudicating those cases by hand.

    # score an AgentLab study directory with both scorers
    python scripts/analysis/rescore_compare.py results/Qwen3-4B/v1_multiTest --judge --limit 50

    # use the open-source alternate judge instead of GPT-5 (serve it first with
    # startVLMmodel.sh; see README "How Tasks are Scored")
    python scripts/analysis/rescore_compare.py results/Qwen3-4B/v1_multiTest --judge --judge-model gemma

    # deterministic only (no API key needed, no cost)
    python scripts/analysis/rescore_compare.py results/Qwen3-4B/v1_multiTest

    # score answers collected elsewhere (JSONL of {"task_id": int, "answer": str})
    python scripts/analysis/rescore_compare.py --answers answers.jsonl

Episodes are read through AgentLab's ``ExpResult``; the answer is the last
assistant chat message, exactly what ``GenericTimeWarpTask.validate`` scores.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "annotation"))

from annotation_lib import DATA_PATH, DATA_V2_PATH, load_tasks, score_answer  # noqa: E402


def extract_episodes(study_dir: Path) -> list:
    """Yield ``{"task_id", "answer", "recorded_reward", "exp_dir"}`` per episode."""
    try:
        from browsergym.experiments.loop import ExpResult
    except ImportError as exc:
        raise SystemExit(
            "reading a study directory needs browsergym-experiments installed "
            f"({exc}); use --answers to score a JSONL of answers instead"
        )

    episodes = []
    for summary_path in sorted(study_dir.rglob("summary_info.json")):
        exp_dir = summary_path.parent
        try:
            result = ExpResult(exp_dir)
            task_name = result.exp_args.env_args.task_name
            if not str(task_name).startswith("timewarp."):
                continue
            task_id = int(str(task_name).split(".")[-1])

            answer = ""
            for step in reversed(result.steps_info or []):
                messages = (step.obs or {}).get("chat_messages") or []
                for message in reversed(messages):
                    if message.get("role") == "assistant":
                        answer = message.get("message", "")
                        break
                if answer:
                    break

            episodes.append(
                {
                    "task_id": task_id,
                    "answer": answer,
                    "recorded_reward": result.summary_info.get("cum_reward"),
                    "exp_dir": str(exp_dir.relative_to(study_dir)),
                }
            )
        except Exception as exc:
            print(f"skipping {exp_dir}: {exc}", file=sys.stderr)
    return episodes


def load_answers(path: Path) -> list:
    episodes = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            record = json.loads(line)
            episodes.append(
                {
                    "task_id": int(record["task_id"]),
                    "answer": record.get("answer", ""),
                    "recorded_reward": record.get("reward"),
                    "exp_dir": record.get("exp_dir", ""),
                }
            )
    return episodes


def judge_score(task: dict, answer: str, model: str | None = None) -> float:
    from annotation_lib import _load_evaluators

    evaluators = _load_evaluators()
    gold = task["eval"]["reference_answers"].get("fuzzy_match", "")
    if not answer.strip() or not gold:
        return 0.0
    if gold == "N/A":
        return float(answer.strip().upper() == "N/A")
    return evaluators.llm_fuzzy_match(answer, gold, task["intent"], model)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_dir", nargs="?", type=Path, help="AgentLab study directory")
    parser.add_argument("--answers", type=Path, help="JSONL of {task_id, answer} instead")
    parser.add_argument("--dataset", type=Path, help="task file to score against")
    parser.add_argument("--judge", action="store_true", help="also run the LLM judge (costs money)")
    parser.add_argument(
        "--judge-model",
        help="judge model or alias (e.g. gpt-5, gemma); default respects $TW_JUDGE, else GPT-5",
    )
    parser.add_argument("--limit", type=int, help="cap the number of episodes judged")
    parser.add_argument("--output", type=Path, help="write the per-episode table as JSON")
    args = parser.parse_args()

    if not args.study_dir and not args.answers:
        parser.error("provide a study directory or --answers")

    dataset = args.dataset or (DATA_V2_PATH if DATA_V2_PATH.exists() else DATA_PATH)
    tasks = {task["task_id"]: task for task in load_tasks(dataset)}
    print(f"scoring against {dataset.name} ({len(tasks)} tasks)")

    episodes = load_answers(args.answers) if args.answers else extract_episodes(args.study_dir)
    if args.limit:
        episodes = episodes[: args.limit]
    print(f"{len(episodes)} episode(s)")

    rows = []
    counts = Counter()
    for episode in episodes:
        task = tasks.get(episode["task_id"])
        if task is None:
            continue
        try:
            deterministic = score_answer(task["eval"], episode["answer"], task["intent"])
        except Exception as exc:
            print(f"task {episode['task_id']}: verifier raised: {exc}", file=sys.stderr)
            deterministic = None

        row = {
            **episode,
            "eval_types": task["eval"]["eval_types"],
            "gold": task["eval"]["reference_answers"].get("fuzzy_match", ""),
            "deterministic": deterministic,
        }
        if args.judge:
            row["judge"] = judge_score(task, episode["answer"], args.judge_model)
            if deterministic is not None:
                if row["judge"] == deterministic:
                    counts["agree"] += 1
                elif row["judge"] > deterministic:
                    counts["judge_only"] += 1
                else:
                    counts["deterministic_only"] += 1
        rows.append(row)

    scored = [r for r in rows if r["deterministic"] is not None]
    if scored:
        passed = sum(1 for r in scored if r["deterministic"] == 1.0)
        print(f"\ndeterministic: {passed}/{len(scored)} passed")
    skipped = len(rows) - len(scored)
    if skipped:
        print(f"{skipped} episode(s) on llm_judge only, not deterministically scored")

    if args.judge and counts:
        print(
            f"\nagreement: {counts['agree']} agree, "
            f"{counts['judge_only']} judge-pass/deterministic-fail, "
            f"{counts['deterministic_only']} deterministic-pass/judge-fail"
        )
        print("\ndisagreements (adjudicate these by hand):")
        for row in rows:
            if row.get("judge") is not None and row["deterministic"] is not None:
                if row["judge"] != row["deterministic"]:
                    print(
                        f"\n  task {row['task_id']} judge={row['judge']} "
                        f"deterministic={row['deterministic']} ({'+'.join(row['eval_types'])})"
                    )
                    print(f"    gold:   {row['gold'][:120]}")
                    print(f"    answer: {row['answer'][:220]}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
