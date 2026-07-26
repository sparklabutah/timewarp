"""Split the TimeWarp task set into work batches.

Annotation batches are stratified by answer shape and site so every annotator
sees the full variety of tasks rather than a block of near-identical ones:

    python scripts/annotation/make_batches.py --batches 16

Spot-check batches are grouped by site instead, because a spot-checker verifies
golds against one environment's content index and loading the wiki index is
expensive:

    python scripts/annotation/make_batches.py --spotcheck
"""

import argparse
from collections import Counter, defaultdict

from annotation_lib import (
    BATCH_DIR,
    OUT_DIR,
    categorize,
    gold_of,
    load_tasks,
    site_key,
    write_json,
)

SPOTCHECK_DIR = OUT_DIR / "spotcheck"

#: Roughly 15 tasks per spot-checker, grouped so each loads one content index.
SPOTCHECK_GROUPS = {"wiki": 5, "news": 3, "webshop": 4, "multi": 4}


def build_batches(tasks: list, count: int) -> list:
    ordered = sorted(tasks, key=lambda t: (categorize(gold_of(t)), site_key(t), t["task_id"]))
    batches = [[] for _ in range(count)]
    for index, task in enumerate(ordered):
        batches[index % count].append(
            {
                "task_id": task["task_id"],
                "intent": task["intent"],
                "additional_instructions": task.get("additional_instructions", ""),
                "sites": task.get("sites", []),
                "gold": gold_of(task),
                "answer_shape": categorize(gold_of(task)),
            }
        )
    return [sorted(batch, key=lambda t: t["task_id"]) for batch in batches]


def task_record(task: dict) -> dict:
    return {
        "task_id": task["task_id"],
        "intent": task["intent"],
        "additional_instructions": task.get("additional_instructions", ""),
        "sites": task.get("sites", []),
        "gold": gold_of(task),
        "answer_shape": categorize(gold_of(task)),
    }


def build_spotcheck_batches(tasks: list) -> dict:
    """Group tasks by the environment a checker must consult."""
    groups = defaultdict(list)
    for task in tasks:
        sites = task.get("sites", [])
        groups["multi" if len(sites) != 1 else sites[0]].append(task_record(task))

    batches = {}
    for group, count in SPOTCHECK_GROUPS.items():
        records = sorted(groups.get(group, []), key=lambda t: t["task_id"])
        for index in range(count):
            chunk = records[index::count]
            if chunk:
                batches[f"{group}_{index + 1}"] = chunk
    return batches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", type=int, default=16)
    parser.add_argument("--spotcheck", action="store_true", help="write site-grouped batches")
    args = parser.parse_args()

    tasks = load_tasks()

    if args.spotcheck:
        batches = build_spotcheck_batches(tasks)
        for name, batch in batches.items():
            write_json(SPOTCHECK_DIR / f"{name}.json", batch)
        print(f"{len(tasks)} tasks -> {len(batches)} spot-check batches in {SPOTCHECK_DIR}")
        for name, batch in sorted(batches.items()):
            print(f"  {name:<12} {len(batch)}")
        return

    batches = build_batches(tasks, args.batches)
    for index, batch in enumerate(batches, start=1):
        write_json(BATCH_DIR / f"batch_{index:02d}.json", batch)

    shapes = Counter(categorize(gold_of(task)) for task in tasks)
    print(f"{len(tasks)} tasks -> {len(batches)} batches in {BATCH_DIR}")
    print("sizes:", [len(batch) for batch in batches])
    print("answer shapes:", dict(shapes.most_common()))


if __name__ == "__main__":
    main()
