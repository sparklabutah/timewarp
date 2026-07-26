"""Structural adversarial audit of merged verifier specs.

The per-batch oracle (selfcheck_eval.py) proves each spec accepts its own gold
and the annotator's examples. This audit is complementary: it probes for
*classes* of mistake that an annotator's own examples might not surface, across
the whole dataset at once. It is deterministic and needs no agent.

    python scripts/annotation/audit_specs.py --data ../../src/browsergym/timewarp/data/test.raw.v2.json

Probes:

* **false-reject / contrastive** — for a spec with a content-word `must_exclude`,
  a correct answer that contrasts the gold with the excluded option
  ("Queensland, not New South Wales") is synthesized and scored. If it is
  rejected, the exclusion may be too broad. Yes/no polarity excludes are
  reported separately because their contrastive form ("Yes, not no") is not a
  natural answer and the exclusion is correct by design.
* **false-accept / echo** — if a `must_include` token is echoed verbatim in the
  intent and the spec is full-scope with no exclusion, a wrong answer that
  merely quotes the question could pass.
* **tolerance** — number tolerances are listed with their gold, so an
  unjustified tolerance (a non-hedged gold) is easy to spot.

Nothing here fails the build; it produces a review list. Write it with --output
and merge_eval_blocks.py folds it into REVIEW.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from annotation_lib import DATA_V2_PATH, gold_of, load_tasks, score_answer, split_or  # noqa: E402

POLARITY = {"yes", "no", "not", "true", "false", "incorrect", "correct"}

CONTRAST_TEMPLATES = [
    "{gold}, not {ex}.",
    "{gold}, unlike {ex}.",
    "{gold} rather than {ex}.",
    "It is {gold}; {ex} is not the answer.",
]


def plain_exclude_tokens(references: dict):
    excludes = references.get("must_exclude", [])
    if isinstance(excludes, str):
        excludes = [excludes]
    for entry in excludes:
        for alt in split_or(entry):
            alt = alt.strip()
            if alt and not alt.startswith("^"):
                yield alt


def block(task: dict) -> dict:
    return {"eval_types": task["eval"]["eval_types"], "reference_answers": task["eval"]["reference_answers"]}


def audit_contrastive(task: dict) -> dict | None:
    references = task["eval"]["reference_answers"]
    gold_head = re.split(r"[,.]", gold_of(task))[0].strip()[:40]
    for token in plain_exclude_tokens(references):
        is_polarity = token.lower() in POLARITY
        for template in CONTRAST_TEMPLATES:
            answer = template.format(gold=gold_head, ex=token)
            try:
                if score_answer(block(task), answer, task["intent"]) == 0.0:
                    return {
                        "task_id": task["task_id"],
                        "kind": "polarity" if is_polarity else "content",
                        "excluded": token,
                        "rejected_answer": answer,
                        "gold": gold_of(task),
                    }
            except Exception:
                continue
    return None


def audit_echo(task: dict) -> dict | None:
    references = task["eval"]["reference_answers"]
    if references.get("scope", "full") != "full" or references.get("must_exclude"):
        return None
    includes = references.get("must_include", [])
    if isinstance(includes, str):
        includes = [includes]
    intent = (task["intent"] + " " + task.get("additional_instructions", "")).lower()
    for entry in includes:
        alts = [a.strip().lower() for a in split_or(entry)]
        if alts and all(len(a) >= 4 and not a.startswith("^") and a in intent for a in alts):
            # An answer that only echoes the question, nothing else.
            if score_answer(block(task), task["intent"], task["intent"]) == 1.0:
                return {"task_id": task["task_id"], "echoed": entry, "gold": gold_of(task)}
    return None


def audit_tolerance(task: dict) -> dict | None:
    spec = task["eval"]["reference_answers"].get("number_match")
    if isinstance(spec, dict) and ("rel_tolerance" in spec or "abs_tolerance" in spec):
        gold = gold_of(task)
        hedged = bool(re.search(r"around|about|over|under|approx|nearly|almost|roughly|\.\d|\bmillion\b|\bbillion\b", gold, re.I))
        return {
            "task_id": task["task_id"],
            "tolerance": {k: spec[k] for k in ("rel_tolerance", "abs_tolerance") if k in spec},
            "gold": gold,
            "gold_looks_hedged": hedged,
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_V2_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    tasks = load_tasks(args.data)
    report = {"contrastive_content": [], "contrastive_polarity": [], "echo": [], "tolerance": []}

    for task in tasks:
        if not any(t != "llm_judge" for t in task["eval"]["eval_types"]):
            continue
        contrast = audit_contrastive(task)
        if contrast:
            key = "contrastive_content" if contrast["kind"] == "content" else "contrastive_polarity"
            report[key].append(contrast)
        echo = audit_echo(task)
        if echo:
            report["echo"].append(echo)
        tolerance = audit_tolerance(task)
        if tolerance:
            report["tolerance"].append(tolerance)

    print(f"content-exclude false-reject candidates: {len(report['contrastive_content'])}")
    for item in report["contrastive_content"]:
        print(f"  task {item['task_id']}: excludes {item['excluded']!r} -> rejects {item['rejected_answer']!r}")
    print(f"\npolarity excludes (expected safe): {len(report['contrastive_polarity'])} tasks")
    print(f"echo false-accept candidates: {len(report['echo'])}")
    for item in report["echo"]:
        print(f"  task {item['task_id']}: echoes {item['echoed']!r}")
    unjustified = [t for t in report["tolerance"] if not t["gold_looks_hedged"]]
    print(f"\nnumber tolerances: {len(report['tolerance'])} ({len(unjustified)} on non-hedged golds)")
    for item in unjustified:
        print(f"  task {item['task_id']}: {item['tolerance']} gold={item['gold']!r}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
