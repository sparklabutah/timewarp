"""Shared helpers for the deterministic-verifier annotation pipeline.

Used by make_batches.py, merge_eval_blocks.py and selfcheck_eval.py.
"""

import importlib.util
import json
import re
import sys
import tempfile
import types
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
PACKAGE_DIR = SRC / "browsergym" / "timewarp"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_PATH = PACKAGE_DIR / "data" / "test.raw.json"
DATA_V2_PATH = PACKAGE_DIR / "data" / "test.raw.v2.json"
OUT_DIR = Path(__file__).resolve().parent / "out"
BATCH_DIR = OUT_DIR / "batches"
ANNOTATION_DIR = OUT_DIR / "annotations"

EVAL_TYPES = ("string_match", "number_match", "list_match", "exact_match", "llm_judge")
DETERMINISTIC_TYPES = tuple(t for t in EVAL_TYPES if t != "llm_judge")
SCOPES = ("full", "first_sentence")
CONFIDENCES = ("high", "medium", "low")


def _load_evaluators():
    """Import the verifier modules without executing ``browsergym.timewarp.__init__``.

    The package's ``__init__`` pulls in nltk, browsergym.core and registers 231
    gym environments. None of that is needed to score an answer, and requiring
    it would make this tooling unusable outside a fully provisioned env.
    """
    try:
        return importlib.import_module("browsergym.timewarp.evaluators")
    except Exception:
        pass

    parent = "timewarp_verifiers"
    if parent not in sys.modules:
        shim = types.ModuleType(parent)
        shim.__path__ = [str(PACKAGE_DIR)]
        sys.modules[parent] = shim

    for name in ("normalization", "evaluators"):
        full_name = f"{parent}.{name}"
        if full_name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(full_name, PACKAGE_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        spec.loader.exec_module(module)

    return sys.modules[f"{parent}.evaluators"]


_OR_RE = re.compile(r"\s*\|OR\|\s*")


def split_or(entry: str) -> list:
    """Split a reference entry on the ``|OR|`` alternative separator."""
    return [part for part in _OR_RE.split(entry) if part.strip()]


def load_tasks(path: Path = DATA_PATH) -> list:
    return json.loads(path.read_text())


def gold_of(task: dict) -> str:
    return task["eval"].get("reference_answers", {}).get("fuzzy_match", "")


def categorize(gold: str) -> str:
    """Coarse answer shape, used to stratify batches and report coverage."""
    text = (gold or "").strip()
    if not text:
        return "empty"
    head = text.lower().lstrip("\"'*(").split(",")[0].split(".")[0].strip()
    if head in ("yes", "no"):
        return "yes_no"
    if "," in text or " and " in text.lower():
        return "list"
    words = text.split()
    if any(char.isdigit() for char in text) and len(words) <= 4:
        return "number"
    if len(words) <= 3:
        return "short_entity"
    return "sentence"


def site_key(task: dict) -> str:
    return "+".join(sorted(task.get("sites", []))) or "none"


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def _check_entries(value, field: str, errors: list) -> None:
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                errors.append(f"{field} entries must be strings, got {item!r}")
        return
    errors.append(f"{field} must be a string or list of strings, got {type(value).__name__}")


def validate_eval_block(block: dict) -> list:
    """Return a list of human-readable problems with an ``eval`` block (empty = valid)."""
    errors = []
    if not isinstance(block, dict):
        return ["eval block must be an object"]

    eval_types = block.get("eval_types")
    if not isinstance(eval_types, list) or not eval_types:
        return ["eval_types must be a non-empty list"]
    for eval_type in eval_types:
        if eval_type not in EVAL_TYPES:
            errors.append(f"unknown eval_type {eval_type!r}")

    references = block.get("reference_answers")
    if not isinstance(references, dict):
        return errors + ["reference_answers must be an object"]

    if "fuzzy_match" not in references:
        errors.append("reference_answers must retain the original 'fuzzy_match' gold")

    if "string_match" in eval_types:
        keys = [k for k in ("exact_match", "must_include", "must_exclude") if k in references]
        if not keys:
            errors.append("string_match needs exact_match, must_include or must_exclude")
        for key in keys:
            _check_entries(references[key], key, errors)
        scope = references.get("scope", "full")
        if scope not in SCOPES:
            errors.append(f"scope must be one of {SCOPES}, got {scope!r}")

    if "number_match" in eval_types:
        spec = references.get("number_match")
        if not isinstance(spec, dict):
            errors.append("number_match requires a 'number_match' object")
        else:
            if "value" not in spec and "values" not in spec:
                errors.append("number_match needs 'value' or 'values'")
            if "values" in spec and (not isinstance(spec["values"], list) or not spec["values"]):
                errors.append("number_match 'values' must be a non-empty list")
            for key in ("rel_tolerance", "abs_tolerance"):
                if key in spec and not isinstance(spec[key], (int, float)):
                    errors.append(f"number_match {key} must be numeric")
            if spec.get("scope", "full") not in SCOPES:
                errors.append(f"number_match scope must be one of {SCOPES}")

    if "list_match" in eval_types:
        spec = references.get("list_match")
        if not isinstance(spec, dict):
            errors.append("list_match requires a 'list_match' object")
        else:
            items = spec.get("items")
            if not isinstance(items, list) or not items:
                errors.append("list_match needs a non-empty 'items' list")
            else:
                for item in items:
                    _check_entries(item, "list_match.items entry", errors)
            if "forbidden" in spec:
                _check_entries(spec["forbidden"], "list_match.forbidden", errors)
            if not isinstance(spec.get("ordered", False), bool):
                errors.append("list_match 'ordered' must be a boolean")
            if spec.get("scope", "full") not in SCOPES:
                errors.append(f"list_match scope must be one of {SCOPES}")

    if "llm_judge" in eval_types and not references.get("fuzzy_match"):
        errors.append("llm_judge requires a non-empty fuzzy_match reference")

    revision = block.get("revision")
    if revision is not None and (not isinstance(revision, int) or revision < 1):
        errors.append("revision must be a positive integer")

    return errors


# --------------------------------------------------------------------------- #
# Scoring (deterministic verifiers only -- never calls an LLM)
# --------------------------------------------------------------------------- #


def score_answer(eval_block: dict, answer: str, intent: str = "") -> Optional[float]:
    """Score ``answer`` against ``eval_block`` using the deterministic verifiers.

    Returns ``None`` for blocks that have no deterministic verifier (llm_judge
    only), so callers can skip them instead of paying for an API call.
    """
    evaluator_router = _load_evaluators().evaluator_router

    deterministic = [t for t in eval_block["eval_types"] if t != "llm_judge"]
    if not deterministic:
        return None

    config = {
        "task_id": 0,
        "intent": intent,
        "goal": intent,
        "eval": {**eval_block, "eval_types": deterministic},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(config, handle)
        path = handle.name
    try:
        evaluator = evaluator_router(path)
        trajectory = [{}, {"action_type": "stop", "answer": answer}]
        return evaluator(trajectory=trajectory, config_file=path, page=None, client=None)
    finally:
        Path(path).unlink(missing_ok=True)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
