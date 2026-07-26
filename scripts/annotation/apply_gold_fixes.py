"""Apply human-reviewed corrections to suspect gold answers and their specs.

Each entry records the environment evidence behind the change. Edits both the
live task gold (reference_answers.fuzzy_match in test.raw.json) and the verifier
spec (in the annotation batch files), then the caller re-merges so the two stay
consistent.

Run once:  python scripts/annotation/apply_gold_fixes.py
"""

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotation_lib import DATA_PATH  # noqa: E402

# task_id -> {gold?, references?, gold_suspect, note}
#   gold        : new fuzzy_match value (omit to leave the gold unchanged)
#   references  : full replacement reference_answers (minus fuzzy_match) (omit to keep)
#   gold_suspect: flag to set after the fix
#   note        : appended provenance
FIXES = {
    3: {
        "gold": "Koalas, kangaroos, wombats, numbats, platypus, short-beaked echidna, bats, seals, dolphins, whales, kiwi, kakapo, tuatara, Moa, rats, dogs, cats, possums.",
        "references": {
            "list_match": {
                "items": [
                    ["koalas |OR| koala"], ["kangaroos |OR| kangaroo"], ["wombats |OR| wombat"],
                    ["numbats |OR| numbat"], ["platypus |OR| platypuses |OR| platypi"],
                    ["echidna |OR| short-beaked echidna"], ["bats |OR| bat"], ["seals |OR| seal"],
                    ["dolphins |OR| dolphin"], ["whales |OR| whale"], ["kiwi |OR| kiwis"],
                    ["kakapo |OR| kakapos"], ["tuatara |OR| tuataras"], ["moa |OR| moas"],
                    ["rats |OR| rat"], ["dogs |OR| dog"], ["cats |OR| cat"], ["possums |OR| possum"],
                ],
                "ordered": False,
                "forbidden": [],
            }
        },
        "gold_suspect": False,
        "note": "FIXED (env-verified): added 'short-beaked echidna', named beside platypus in Australia's 'Indigenous life' section. All other gold animals confirmed across the two sections.",
    },
    7: {
        "gold": "In politics, a is the government of a country which has control over a geographic area or territory.",
        "gold_suspect": False,
        "note": "FIXED (env-verified): removed the spurious 'State ' prefix; the article renders 'In politics, a is the government of a country which has control over a geographic area or territory.' NOTE the env HTML drops the word 'state' ('a is' rather than 'a state is') -- an environment bug, but the gold now matches what an agent actually reads. Spec anchors on stable tokens.",
    },
    9: {
        "gold": "Periodic table, Atomic number, Atomic nucleus, Proton, Neutron, Atom, Solid",
        "gold_suspect": False,
        "note": "FIXED (env-verified): item 3 corrected from link text 'nucleus' to the actual page title 'Atomic nucleus' (Atomic number's third link points to /wiki/atomic nucleus; a separate 'Nucleus' page also exists). Spec already accepts both spellings.",
    },
    14: {
        "gold_suspect": False,
        "note": "VERIFIED CORRECT (env): only Queensland (floral + fauna) and South Australia (floral + faunal) mention floral/faunal emblems -> 4 total; New South Wales, Victoria, Western Australia and Tasmania articles mention none. Gold 'Four' stands.",
    },
    19: {
        "gold": "election",
        "references": {
            "must_include": ["election |OR| name |OR| given name"],
            "scope": "first_sentence",
        },
        "gold_suspect": False,
        "note": "FIXED (env-verified): old gold 'Suffrage' restated the anchor rather than the word before it. In Democracy '...vote in an election. Suffrage is...' so 'election' precedes Suffrage; in Name '...the given name. \"Suzuki Ichiro\"...' so 'name' precedes Suzuki Ichiro. The intent says 'either ... or', so both are acceptable and the spec accepts either.",
    },
    52: {
        "gold_suspect": False,
        "note": "GOLD CORRECT ('Toronto', env-verified). Remaining concern is task executability, not the gold: the search engine's tokenizer may drop the accented query 'Pokemon'. Left for human review of the task, not the answer.",
    },
    99: {
        "gold": "American Girl dolls; not available in the shop.",
        "references": {
            "must_include": [
                "american girl",
                "^.*\\bnot\\b[^.]{0,40}\\b(?:availab\\w*|find|found|sold|sell\\w*|listed|carr\\w+|stock\\w*|offered|exist\\w*|have|has|there|in the shop)\\b.*$ |OR| unavailable |OR| no american girl |OR| no results |OR| no such product |OR| out of stock",
            ],
            "scope": "full",
        },
        "gold_suspect": False,
        "note": "FIXED (env-verified): the Mattel article lists 'American Girl dolls' before 'Barbie dolls', and the intent asks for the FIRST product mentioned. Shop search for 'American Girl' returns 0 products, so the 'not available' half stands.",
    },
    155: {
        "gold_suspect": False,
        "note": "GOLD DEFENSIBLE: the additional_instructions direct the agent to report the publication date, which the gold gives. The intent alone reads as 'which article', but agents receive intent + instructions together. Left unchanged.",
    },
    # 96 and 158 intentionally NOT auto-fixed -- see the escalation note printed below.
}

ESCALATE = {
    96: "Order-code gold vs. a plausible negative biscuit article ('Fiji ... ban on Fijian biscuits'). Flipping the task branch is a judgement about whether a trade-ban story counts as 'bad news about biscuits'; needs a human decision. Left flagged, gold unchanged.",
    158: "Gold quotes phrases the environment's HTML has dropped ('serial killer', 'sentenced to death'). This is an ENVIRONMENT bug, not a gold error; fixing the rendered article is the real remedy. Spec already anchors on tokens that render. Left flagged, gold unchanged.",
}


def main() -> int:
    tasks = json.loads(DATA_PATH.read_text())
    by_id = {t["task_id"]: t for t in tasks}

    # 1) golds in the live task file
    changed_golds = []
    for tid, fix in FIXES.items():
        if "gold" in fix:
            by_id[tid]["eval"]["reference_answers"]["fuzzy_match"] = fix["gold"]
            changed_golds.append(tid)
    DATA_PATH.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")
    print(f"updated {len(changed_golds)} golds in {DATA_PATH.name}: {changed_golds}")

    # 2) specs, flags and notes in the annotation batch files
    ann_dir = Path(__file__).resolve().parent / "out" / "annotations"
    touched = 0
    for path in sorted(ann_dir.glob("batch_*.json")):
        records = json.loads(path.read_text())
        dirty = False
        for rec in records:
            fix = FIXES.get(rec["task_id"])
            if not fix:
                if rec["task_id"] in ESCALATE:  # keep flagged, annotate why
                    rec["gold_suspect"] = True
                    if ESCALATE[rec["task_id"]] not in rec.get("notes", ""):
                        rec["notes"] = (rec.get("notes", "") + " | ESCALATED: " + ESCALATE[rec["task_id"]]).strip(" |")
                        dirty = True
                continue
            if "references" in fix:
                rec["reference_answers"] = fix["references"]
            rec["gold_suspect"] = fix["gold_suspect"]
            if fix["note"] not in rec.get("notes", ""):
                rec["notes"] = (rec.get("notes", "") + " | " + fix["note"]).strip(" |")
            dirty = True
        if dirty:
            path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
            touched += 1
    print(f"updated specs/flags in {touched} annotation files")
    print(f"\nstill flagged for human decision: {sorted(ESCALATE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
