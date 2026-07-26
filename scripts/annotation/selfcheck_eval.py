"""Execute deterministic verifier specs against known-good and known-bad answers.

Three modes:

    # score one ad-hoc spec against one answer (for interactive spec design)
    python scripts/annotation/selfcheck_eval.py --spec '{"eval_types": ["string_match"],
        "reference_answers": {"must_include": ["alaska"]}}' --answer "It is Alaska."

    # check every annotation in a batch file (or all of out/annotations/)
    python scripts/annotation/selfcheck_eval.py --input out/annotations/batch_03.json

    # check the shipped dataset: every gold must satisfy its own verifier
    python scripts/annotation/selfcheck_eval.py --dataset

Checks applied to each annotation:

* **gold**       the task's original gold answer must score 1.0
* **positive**   every ``positive_examples`` entry must score 1.0
* **negative**   every ``negative_examples`` entry must score 0.0
* **crosstalk**  the spec is scored against other tasks' golds; a spec that
                 accepts many of them is too lenient to discriminate

Exit status is non-zero when any check fails, so it can gate a merge.
"""

import argparse
import json
import random
import sys
from pathlib import Path

from annotation_lib import (
    ANNOTATION_DIR,
    DATA_PATH,
    gold_of,
    load_tasks,
    score_answer,
    validate_eval_block,
    write_json,
)

CROSSTALK_SAMPLE = 40
CROSSTALK_WARN_RATE = 0.15


def build_eval_block(annotation: dict, gold: str) -> dict:
    """Assemble the runtime eval block: annotation spec + the preserved gold."""
    references = dict(annotation.get("reference_answers") or {})
    references["fuzzy_match"] = gold
    return {"eval_types": list(annotation["eval_types"]), "reference_answers": references}


def check_annotation(annotation: dict, task: dict, others: list) -> dict:
    gold = gold_of(task)
    block = build_eval_block(annotation, gold)
    result = {
        "task_id": annotation["task_id"],
        "eval_types": block["eval_types"],
        "confidence": annotation.get("confidence"),
        "failures": [],
        "warnings": [],
    }

    schema_errors = validate_eval_block(block)
    if schema_errors:
        result["failures"].extend(f"schema: {error}" for error in schema_errors)
        return result

    if not [t for t in block["eval_types"] if t != "llm_judge"]:
        result["deterministic"] = False
        return result
    result["deterministic"] = True

    intent = task["intent"]

    def score(answer):
        try:
            return score_answer(block, answer, intent)
        except Exception as exc:  # a malformed spec must surface, not pass silently
            result["failures"].append(f"raised on {answer!r}: {exc}")
            return None

    gold_score = score(gold)
    if gold_score is not None and gold_score != 1.0:
        result["failures"].append(f"gold answer {gold!r} scores {gold_score}")

    for example in annotation.get("positive_examples", []):
        value = score(example)
        if value is not None and value != 1.0:
            result["failures"].append(f"positive example rejected: {example!r}")

    for example in annotation.get("negative_examples", []):
        value = score(example)
        if value is not None and value != 0.0:
            result["failures"].append(f"negative example accepted: {example!r}")

    accepted = []
    for other in others:
        other_gold = gold_of(other)
        if not other_gold or other_gold.strip().lower() == gold.strip().lower():
            continue
        if score(other_gold) == 1.0:
            accepted.append(other["task_id"])
    if accepted:
        rate = len(accepted) / max(1, len(others))
        result["crosstalk"] = {"rate": round(rate, 3), "task_ids": accepted[:10]}
        if rate > CROSSTALK_WARN_RATE:
            result["warnings"].append(
                f"accepts {len(accepted)}/{len(others)} unrelated golds -- likely too lenient"
            )

    return result


def load_annotations(paths: list) -> list:
    annotations = []
    for path in paths:
        payload = json.loads(Path(path).read_text())
        if isinstance(payload, dict):
            payload = payload.get("annotations", [])
        annotations.extend(payload)
    return annotations


def run_checks(annotations: list, tasks: list, seed: int = 13) -> dict:
    by_id = {task["task_id"]: task for task in tasks}
    random.seed(seed)
    results = []
    for annotation in annotations:
        task = by_id.get(annotation["task_id"])
        if task is None:
            results.append(
                {"task_id": annotation["task_id"], "failures": ["unknown task_id"], "warnings": []}
            )
            continue
        pool = [t for t in tasks if t["task_id"] != annotation["task_id"]]
        others = random.sample(pool, min(CROSSTALK_SAMPLE, len(pool)))
        results.append(check_annotation(annotation, task, others))

    failed = [r for r in results if r["failures"]]
    warned = [r for r in results if r["warnings"] and not r["failures"]]
    return {
        "checked": len(results),
        "failed": len(failed),
        "warned": len(warned),
        "results": results,
    }


def print_report(report: dict, verbose: bool) -> None:
    print(
        f"checked {report['checked']} annotations: "
        f"{report['failed']} failing, {report['warned']} with warnings"
    )
    for result in report["results"]:
        if result["failures"]:
            print(f"\nFAIL task {result['task_id']} ({', '.join(result.get('eval_types', []))})")
            for failure in result["failures"]:
                print(f"    - {failure}")
        elif result["warnings"] and verbose:
            print(f"\nWARN task {result['task_id']}")
            for warning in result["warnings"]:
                print(f"    - {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", help="JSON eval block to score ad hoc")
    parser.add_argument("--answer", help="answer text to score against --spec")
    parser.add_argument("--input", nargs="*", help="annotation JSON file(s)")
    parser.add_argument("--dataset", action="store_true", help="check the shipped dataset's golds")
    parser.add_argument("--report", help="write the full JSON report here")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.spec:
        if args.answer is None:
            parser.error("--spec requires --answer")
        block = json.loads(args.spec)
        block.setdefault("reference_answers", {}).setdefault("fuzzy_match", "")
        print(score_answer(block, args.answer))
        return 0

    tasks = load_tasks()

    if args.dataset:
        annotations = [
            {
                "task_id": task["task_id"],
                "eval_types": task["eval"]["eval_types"],
                "reference_answers": task["eval"]["reference_answers"],
            }
            for task in load_tasks(DATA_PATH)
        ]
    else:
        paths = args.input or sorted(str(p) for p in ANNOTATION_DIR.glob("batch_*.json"))
        if not paths:
            parser.error(f"no annotation files found in {ANNOTATION_DIR}")
        annotations = load_annotations(paths)

    report = run_checks(annotations, tasks)
    print_report(report, args.verbose)
    if args.report:
        write_json(Path(args.report), report)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
