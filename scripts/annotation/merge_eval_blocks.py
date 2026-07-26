"""Merge annotated verifier specs into the TimeWarp task dataset.

    # build data/test.raw.v2.json from out/annotations/*.json and report coverage
    python scripts/annotation/merge_eval_blocks.py

    # validate the shipped dataset without writing anything
    python scripts/annotation/merge_eval_blocks.py --validate-only

The merge preserves each task's original ``fuzzy_match`` gold so runs stay A/B
comparable and a rollback is a one-line change, stamps ``revision`` and carries
the annotator's provenance in ``annotation``.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from annotation_lib import (
    ANNOTATION_DIR,
    DATA_PATH,
    DATA_V2_PATH,
    categorize,
    gold_of,
    load_tasks,
    site_key,
    validate_eval_block,
    write_json,
)

REVIEW_PATH = Path(__file__).resolve().parent / "REVIEW.md"


def load_annotations(directory: Path) -> dict:
    annotations = {}
    duplicates = []
    # Only batch_*.json — the finished annotations. Ignore stray draft_/report
    # files that may share the directory, so task ids can't be double-counted.
    for path in sorted(directory.glob("batch_*.json")):
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("annotations", [])
        for record in payload:
            task_id = record["task_id"]
            if task_id in annotations:
                duplicates.append(task_id)
            record.setdefault("_source", path.name)
            annotations[task_id] = record
    if duplicates:
        print(f"warning: duplicate annotations for task ids {sorted(set(duplicates))}")
    return annotations


def merge_task(task: dict, annotation: dict) -> dict:
    """Return ``task`` with its eval block replaced by the annotated verifier spec."""
    gold = gold_of(task)
    references = dict(annotation.get("reference_answers") or {})
    references.pop("fuzzy_match", None)
    references["fuzzy_match"] = gold

    merged = dict(task)
    merged["eval"] = {
        "eval_types": list(annotation["eval_types"]),
        "reference_answers": references,
        "revision": int(annotation.get("revision", 1)),
        "annotation": {
            "confidence": annotation.get("confidence", "unknown"),
            "subjective": bool(annotation.get("subjective", False)),
            "gold_suspect": bool(annotation.get("gold_suspect", False)),
            "notes": annotation.get("notes", ""),
            "source": annotation.get("_source", ""),
        },
    }
    return merged


def coverage(tasks: list) -> dict:
    by_type = Counter()
    by_site = defaultdict(Counter)
    by_shape = defaultdict(Counter)
    deterministic = 0

    for task in tasks:
        types = task["eval"]["eval_types"]
        label = "llm_judge" if types == ["llm_judge"] else "+".join(types)
        by_type[label] += 1
        is_deterministic = any(t != "llm_judge" for t in types)
        deterministic += int(is_deterministic)
        bucket = "deterministic" if is_deterministic else "llm_judge"
        by_site[site_key(task)][bucket] += 1
        by_shape[categorize(gold_of(task))][bucket] += 1

    return {
        "total": len(tasks),
        "deterministic": deterministic,
        "llm_judge": len(tasks) - deterministic,
        "pct": round(100 * deterministic / max(1, len(tasks)), 1),
        "by_type": dict(by_type.most_common()),
        "by_site": {k: dict(v) for k, v in sorted(by_site.items())},
        "by_shape": {k: dict(v) for k, v in sorted(by_shape.items())},
    }


def print_coverage(stats: dict) -> None:
    print(
        f"\ndeterministic coverage: {stats['deterministic']}/{stats['total']} "
        f"({stats['pct']}%)  |  llm_judge fallback: {stats['llm_judge']}"
    )
    print("\nby verifier combination:")
    for label, count in stats["by_type"].items():
        print(f"  {label:<34} {count}")
    print("\nby answer shape (deterministic / llm_judge):")
    for shape, counts in stats["by_shape"].items():
        print(f"  {shape:<16} {counts.get('deterministic', 0):>4} / {counts.get('llm_judge', 0)}")
    print("\nby site (deterministic / llm_judge):")
    for site, counts in stats["by_site"].items():
        print(f"  {site:<22} {counts.get('deterministic', 0):>4} / {counts.get('llm_judge', 0)}")


def write_review(tasks: list, annotations: dict, stats: dict, report: dict, spotcheck: dict, audit: dict) -> None:
    flagged = {"gold_suspect": [], "subjective": [], "low": [], "medium": []}
    for task in tasks:
        meta = task["eval"].get("annotation", {})
        task_id = task["task_id"]
        if meta.get("gold_suspect"):
            flagged["gold_suspect"].append(task_id)
        if meta.get("subjective"):
            flagged["subjective"].append(task_id)
        confidence = meta.get("confidence")
        if confidence in ("low", "medium"):
            flagged[confidence].append(task_id)

    by_id = {task["task_id"]: task for task in tasks}
    warned = {
        result["task_id"]: result["warnings"]
        for result in report.get("results", [])
        if result.get("warnings")
    }

    lines = [
        "# Verifier annotation review",
        "",
        "Generated by `scripts/annotation/merge_eval_blocks.py`. Everything here",
        "needs a human decision; nothing in this list blocks the merge.",
        "",
        "## Coverage",
        "",
        f"- deterministic: **{stats['deterministic']}/{stats['total']} ({stats['pct']}%)**",
        f"- llm_judge fallback: {stats['llm_judge']}",
        f"- gold spot-checked against environment content: "
        f"{spotcheck.get('agree', 0) + len(spotcheck.get('findings', [])) + spotcheck.get('uncheckable', 0)}"
        f"/{stats['total']} "
        f"(the remainder were not spot-checked; re-run `timewarp-gold-spotcheck` to finish)",
        "",
    ]

    def section(title, task_ids, blurb):
        lines.extend([f"## {title} ({len(task_ids)})", "", blurb, ""])
        if not task_ids:
            lines.extend(["_None._", ""])
            return
        lines.append("| task | gold | verifier | note |")
        lines.append("|---|---|---|---|")
        for task_id in sorted(task_ids):
            task = by_id[task_id]
            meta = task["eval"].get("annotation", {})
            gold = gold_of(task).replace("|", "\\|")[:70]
            types = "+".join(task["eval"]["eval_types"])
            note = meta.get("notes", "").replace("|", "\\|").replace("\n", " ")[:160]
            lines.append(f"| {task_id} | {gold} | {types} | {note} |")
        lines.append("")

    section(
        "Suspect gold answers",
        flagged["gold_suspect"],
        "The annotator believes the gold does not answer the intent. The gold was "
        "**not** changed. Confirm against the live environment before editing.",
    )
    section(
        "Left on the LLM judge",
        flagged["subjective"],
        "No deterministic spec was found. Each is a candidate for rewriting the "
        "intent so the answer becomes objectively checkable.",
    )
    section(
        "Low confidence",
        flagged["low"],
        "The annotator was unsure the spec is correct.",
    )
    section(
        "Medium confidence",
        flagged["medium"],
        "Usually a low-discriminative gold (a common word or a small integer) or a "
        "`must_exclude` that required judgement.",
    )

    contrastive = audit.get("contrastive_content", [])
    lines.extend(
        [
            f"## `must_exclude` false-reject candidates ({len(contrastive)})",
            "",
            "Found by `scripts/annotation/audit_specs.py`. Each spec rejects a *wrong* "
            "answer by excluding a token, but would also reject an unusual **correct** "
            "answer that contrasts the gold with that token (\"Queensland, not New South "
            "Wales\"). This is a deliberate trade-off — the exclusion is what rejects the "
            "common partial/wrong answers — but the phrasings below are worth a look. "
            "Polarity excludes (yes/no) were audited and are safe.",
            "",
        ]
    )
    if contrastive:
        lines.extend(["| task | excludes | would reject |", "|---|---|---|"])
        for item in sorted(contrastive, key=lambda i: i["task_id"]):
            excl = str(item["excluded"]).replace("|", "\\|")
            ans = str(item["rejected_answer"]).replace("|", "\\|")
            lines.append(f"| {item['task_id']} | `{excl}` | {ans} |")
    else:
        lines.append("_None._")
    lines.append("")

    echoes = audit.get("echo", [])
    if echoes:
        lines.extend(
            [
                f"## `must_include` echo false-accept candidates ({len(echoes)})",
                "",
                "The required token is quoted verbatim in the task intent, so an answer that "
                "merely restates the question could pass. Usually benign when the intent "
                "dictates the exact answer to give.",
                "",
                "| task | echoed token |",
                "|---|---|",
            ]
        )
        for item in sorted(echoes, key=lambda i: i["task_id"]):
            lines.append(f"| {item['task_id']} | `{str(item['echoed'])[:80]}` |")
        lines.append("")

    findings = spotcheck.get("findings", [])
    lines.extend(
        [
            f"## Golds contradicted by environment content ({len(findings)})",
            "",
            "Found by reading the wiki/news/webshop content directly "
            "(`scripts/annotation/env_lookup.py`). These golds were **not** changed. "
            "A wrong gold is far more damaging under a strict verifier than under the "
            "old LLM judge, so these deserve a decision before the swap.",
            "",
        ]
    )
    if findings:
        lines.extend(["| task | gold | suggested | problem | evidence |", "|---|---|---|---|---|"])
        for finding in sorted(findings, key=lambda f: f["task_id"]):

            def cell(value, limit=200):
                return str(value).replace("|", "\\|").replace("\n", " ")[:limit]

            lines.append(
                f"| {finding['task_id']} | {cell(finding.get('gold'), 60)} "
                f"| {cell(finding.get('suggested_gold'), 60)} "
                f"| {cell(finding.get('problem'))} | {cell(finding.get('evidence'), 260)} |"
            )
    else:
        lines.append("_None._")
    lines.append("")

    if spotcheck:
        lines.extend(
            [
                f"Spot-check coverage: {spotcheck.get('agree', 0)} golds confirmed, "
                f"{len(findings)} suspicious, {spotcheck.get('uncheckable', 0)} not decidable "
                "from static content (navigation- or ranking-dependent tasks).",
                "",
            ]
        )

    lines.extend(
        [
            f"## Cross-task leniency warnings ({len(warned)})",
            "",
            "These specs also accept some unrelated tasks' gold answers, which means "
            "they discriminate weakly. Often unavoidable for one-word golds.",
            "",
        ]
    )
    if warned:
        lines.extend(["| task | warning |", "|---|---|"])
        for task_id in sorted(warned):
            for warning in warned[task_id]:
                lines.append(f"| {task_id} | {warning} |")
    else:
        lines.append("_None._")
    lines.append("")

    REVIEW_PATH.write_text("\n".join(lines))
    print(f"\nreview report -> {REVIEW_PATH}")


def validate_tasks(tasks: list) -> int:
    """Validate schemas and confirm every task builds a live evaluator."""
    from annotation_lib import _load_evaluators

    evaluator_router = _load_evaluators().evaluator_router
    import tempfile

    problems = 0
    for task in tasks:
        errors = validate_eval_block(task["eval"])
        for error in errors:
            print(f"task {task['task_id']}: {error}")
            problems += 1
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(task, handle)
            path = handle.name
        try:
            evaluator_router(path)
        except Exception as exc:
            print(f"task {task['task_id']}: router failed: {exc}")
            problems += 1
        finally:
            Path(path).unlink(missing_ok=True)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--annotations", type=Path, default=ANNOTATION_DIR)
    parser.add_argument("--output", type=Path, default=DATA_V2_PATH)
    parser.add_argument("--report", type=Path, help="selfcheck JSON report, for the review file")
    parser.add_argument("--spotcheck", type=Path, help="gold spot-check findings JSON")
    parser.add_argument("--audit", type=Path, help="audit_specs.py findings JSON")
    args = parser.parse_args()

    if args.validate_only:
        tasks = load_tasks(DATA_PATH)
        problems = validate_tasks(tasks)
        print_coverage(coverage(tasks))
        print(f"\n{problems} problem(s) in {DATA_PATH.name}")
        return 1 if problems else 0

    tasks = load_tasks(DATA_PATH)
    annotations = load_annotations(args.annotations)

    missing = [task["task_id"] for task in tasks if task["task_id"] not in annotations]
    if missing:
        print(f"ERROR: {len(missing)} task(s) have no annotation: {missing}")
        return 1

    merged = [merge_task(task, annotations[task["task_id"]]) for task in tasks]
    problems = validate_tasks(merged)
    if problems:
        print(f"\nERROR: {problems} validation problem(s); not writing {args.output.name}")
        return 1

    write_json(args.output, merged)
    print(f"wrote {len(merged)} tasks -> {args.output}")

    stats = coverage(merged)
    print_coverage(stats)

    def read_optional(path):
        return json.loads(path.read_text()) if path and path.exists() else {}

    write_review(
        merged,
        annotations,
        stats,
        read_optional(args.report),
        read_optional(args.spotcheck),
        read_optional(args.audit),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
