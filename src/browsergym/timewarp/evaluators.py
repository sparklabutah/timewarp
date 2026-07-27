"""
TimeWarp Evaluators
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Union, Any, NamedTuple, Optional

from playwright.sync_api import Page

from .normalization import (
    as_entry_list,
    contains_entry,
    equals_entry,
    extract_numbers,
    find_entry,
    numbers_match,
    scope_text,
    to_decimal,
)

logger = logging.getLogger(__name__)


def _load_config(config_file: Union[Path, str]) -> dict:
    with open(config_file, "r") as f:
        return json.load(f)


class Evaluator:
    """Base evaluator class"""

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page,
        client=None,
    ) -> float:
        raise NotImplementedError

    @staticmethod
    def get_last_action(trajectory: list) -> dict:
        try:
            return trajectory[-1]
        except Exception:
            raise ValueError("Trajectory should have at least one action")

    @staticmethod
    def clean_answer(answer: str) -> str:
        """Clean and normalize answer for robust matching.

        - Strips leading/trailing whitespace
        - Removes surrounding quotes
        - Normalizes internal whitespace (multiple spaces/tabs/newlines -> single space)
        - Converts to lowercase
        """
        answer = answer.strip()
        if answer.startswith("'") and answer.endswith("'"):
            answer = answer[1:-1]
        elif answer.startswith('"') and answer.endswith('"'):
            answer = answer[1:-1]
        # Normalize all whitespace (spaces, tabs, newlines) to single spaces
        answer = re.sub(r"\s+", " ", answer)
        # Strip again after normalization in case quotes removal left whitespace
        answer = answer.strip()
        return answer.lower()


class ExactMatchEvaluator(Evaluator):
    """Exact match evaluator with robust normalization.

    Performs case-insensitive matching with whitespace normalization:
    - Converts to lowercase
    - Strips leading/trailing whitespace
    - Normalizes internal whitespace (multiple spaces/tabs/newlines -> single space)
    - Removes surrounding quotes
    """

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page | None = None,
        client=None,
    ) -> float:
        with open(config_file, "r") as f:
            configs = json.load(f)

        last_action = self.get_last_action(trajectory)
        pred = self.clean_answer(last_action.get("answer", ""))

        ref_answers = configs["eval"].get("reference_answers", {})

        if "exact_match" in ref_answers:
            ref = self.clean_answer(ref_answers["exact_match"])
            return float(pred == ref)

        return 0.0


class DeterministicEvaluator(Evaluator):
    """Base class for verifiers that score a free-text answer without an LLM.

    Subclasses read their configuration from ``config["eval"]["reference_answers"]``
    and must raise :class:`ValueError` on a malformed spec rather than returning
    0.0 -- a silent zero is indistinguishable from a genuinely failed episode.
    """

    #: Key inside ``reference_answers`` holding this verifier's spec, if nested.
    spec_key: str = ""

    def _answer(self, trajectory: list, scope: str) -> str:
        raw = self.get_last_action(trajectory).get("answer", "")
        return scope_text(raw, scope)

    def _references(self, config_file: Union[Path, str]) -> dict:
        configs = _load_config(config_file)
        references = configs.get("eval", {}).get("reference_answers")
        if not isinstance(references, dict):
            raise ValueError(
                f"{type(self).__name__} requires an 'eval.reference_answers' object "
                f"(task_id={configs.get('task_id')})"
            )
        return references


class StringMatchEvaluator(DeterministicEvaluator):
    """Match a free-text answer against string references.

    Supported keys inside ``reference_answers``:

    ``exact_match``
        String or list of strings; the normalized answer must equal *any* of
        them. Use only when the answer is expected to be a bare value.
    ``must_include``
        List of entries that must *all* appear in the answer, matched on word
        boundaries. Each entry may offer ``" |OR| "`` alternatives.
    ``must_exclude``
        List of entries that must *not* appear. Reserved for tokens that cannot
        occur in any correct answer (e.g. the wrong option of a multiple choice).
    ``scope``
        ``"full"`` (default) or ``"first_sentence"``.

    Entries written as ``^...$`` are treated as regexes over the normalized text.
    """

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page | None = None,
        client=None,
    ) -> float:
        references = self._references(config_file)
        scope = references.get("scope", "full")
        answer = self._answer(trajectory, scope)

        exact = as_entry_list(references.get("exact_match"), "exact_match")
        includes = as_entry_list(references.get("must_include"), "must_include")
        excludes = as_entry_list(references.get("must_exclude"), "must_exclude")

        if not (exact or includes or excludes):
            raise ValueError(
                "string_match requires at least one of 'exact_match', "
                "'must_include' or 'must_exclude' in reference_answers"
            )

        if exact and not any(equals_entry(answer, entry) for entry in exact):
            logger.debug("string_match: no exact_match alternative matched %r", answer)
            return 0.0

        for entry in includes:
            if not contains_entry(answer, entry):
                logger.debug("string_match: missing required %r in %r", entry, answer)
                return 0.0

        for entry in excludes:
            if contains_entry(answer, entry):
                logger.debug("string_match: forbidden %r present in %r", entry, answer)
                return 0.0

        return 1.0


class NumberMatchEvaluator(DeterministicEvaluator):
    """Match numeric answers regardless of formatting.

    Spec lives at ``reference_answers.number_match``::

        {"value": 7000000, "rel_tolerance": 0.1}
        {"values": [5, 1.8], "abs_tolerance": 0.01}

    Every required value must be found among the numbers parsed out of the
    answer. Comparison is exact unless a tolerance is given; ``values`` entries
    may be bare numbers or objects carrying their own tolerances.
    """

    spec_key = "number_match"

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page | None = None,
        client=None,
    ) -> float:
        references = self._references(config_file)
        spec = references.get(self.spec_key)
        if not isinstance(spec, dict):
            raise ValueError("number_match requires a 'number_match' object in reference_answers")

        answer = self._answer(trajectory, spec.get("scope", "full"))
        default_rel = spec.get("rel_tolerance")
        default_abs = spec.get("abs_tolerance")

        if "values" in spec:
            raw_requirements = spec["values"]
            if not isinstance(raw_requirements, list) or not raw_requirements:
                raise ValueError("number_match 'values' must be a non-empty list")
        elif "value" in spec:
            raw_requirements = [spec["value"]]
        else:
            raise ValueError("number_match requires a 'value' or 'values' key")

        candidates = extract_numbers(answer)
        if not candidates:
            logger.debug("number_match: no numbers found in %r", answer)
            return 0.0

        for requirement in raw_requirements:
            if isinstance(requirement, dict):
                expected = to_decimal(requirement["value"])
                rel = requirement.get("rel_tolerance", default_rel)
                abs_ = requirement.get("abs_tolerance", default_abs)
            else:
                expected = to_decimal(requirement)
                rel, abs_ = default_rel, default_abs

            if not any(numbers_match(c, expected, rel, abs_) for c in candidates):
                logger.debug("number_match: %s not found among %s", expected, candidates)
                return 0.0

        return 1.0


class ListMatchEvaluator(DeterministicEvaluator):
    """Check that an answer enumerates every element of a reference list.

    Spec lives at ``reference_answers.list_match``::

        {"items": [["koalas"], ["kangaroos |OR| kangaroo"]],
         "ordered": false,
         "forbidden": []}

    Each item is a list of interchangeable spellings (a bare string is accepted
    as a one-element list); every item must appear in the answer. With
    ``ordered: true`` the items' first occurrences must appear in the given
    order, which is how sequence answers (navigation paths, rankings) are
    checked. ``forbidden`` entries must not appear at all.
    """

    spec_key = "list_match"

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page | None = None,
        client=None,
    ) -> float:
        references = self._references(config_file)
        spec = references.get(self.spec_key)
        if not isinstance(spec, dict):
            raise ValueError("list_match requires a 'list_match' object in reference_answers")

        items = spec.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("list_match requires a non-empty 'items' list")

        answer = self._answer(trajectory, spec.get("scope", "full"))
        ordered = bool(spec.get("ordered", False))

        offsets = []
        for item in items:
            alternatives = as_entry_list(item, "list_match.items entry")
            if not alternatives:
                raise ValueError("list_match items must not be empty")
            matches = [
                offset
                for alternative in alternatives
                for offset in (find_entry(answer, alternative),)
                if offset is not None
            ]
            if not matches:
                logger.debug("list_match: missing item %r in %r", alternatives, answer)
                return 0.0
            offsets.append(min(matches))

        if ordered and any(a >= b for a, b in zip(offsets, offsets[1:])):
            logger.debug("list_match: items out of order (offsets=%s)", offsets)
            return 0.0

        for entry in as_entry_list(spec.get("forbidden"), "list_match.forbidden"):
            if contains_entry(answer, entry):
                logger.debug("list_match: forbidden %r present in %r", entry, answer)
                return 0.0

        return 1.0


def _normalize_openai_response_text(response: Any) -> str:
    """Extract text content from various possible return types of the OpenAI API."""
    # If it's already a string
    if isinstance(response, str):
        return response

    # If it's an SDK-like object with `choices`
    try:
        choices = getattr(response, "choices", None)
        if choices:
            first_choice = choices[0]
            # Try message.content (chat) then text (completion)
            message = getattr(first_choice, "message", None)
            if message is None and isinstance(first_choice, dict):
                message = first_choice.get("message")
            if message is not None:
                content = getattr(message, "content", None)
                if content is None and isinstance(message, dict):
                    content = message.get("content")
                if content:
                    return content
            text = getattr(first_choice, "text", None)
            if text is None and isinstance(first_choice, dict):
                text = first_choice.get("text")
            if text:
                return text
    except Exception:
        pass

    # If it's a plain dict, try common keys
    if isinstance(response, dict):
        # Direct content
        if "content" in response and isinstance(response["content"], str):
            return response["content"]
        # choices-like dict
        if "choices" in response and response["choices"]:
            first_choice = response["choices"][0]
            if isinstance(first_choice, dict):
                msg = first_choice.get("message", {})
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    return msg["content"]
                if isinstance(first_choice.get("text"), str):
                    return first_choice["text"]

    # Fallback: stringify
    return str(response)


# --- LLM judge selection ------------------------------------------------------
#
# The paper scores the residual, non-deterministically checkable tasks with an
# LLM judge. GPT-5 is the primary judge; an open-source model (Gemma) is offered
# as an alternate so the results reproduce without a proprietary API and so the
# paper can report judge agreement across an open/closed pair.
#
# A GPT / o-series id is sent to the OpenAI API (OPENAI_API_KEY). Anything else is
# assumed to be an open-weights checkpoint served behind an OpenAI-compatible
# endpoint (vLLM via ``startVLMmodel.sh``, Ollama, ...) and is routed there with a
# throwaway key. Every knob is overridable by env var so the alternate judge can
# be pointed at a running server without editing any task config.

#: Primary judge used throughout the paper.
DEFAULT_JUDGE_MODEL = "gpt-5.1-2025-11-13"

#: Open-source alternate. The value is the id the serving stack advertises; for
#: vLLM that is the ``--model`` argument (an HF repo id or a local path).
#: Override with ``TW_JUDGE_MODEL`` if you serve a different checkpoint/revision.
GEMMA_JUDGE_MODEL = "google/gemma-4-12b-it"

#: Friendly aliases accepted anywhere a judge is named (``TW_JUDGE`` env var, a
#: task's ``eval.llm_model``, ``rescore_compare.py --judge-model``).
JUDGE_ALIASES = {
    "gpt": DEFAULT_JUDGE_MODEL,
    "gpt-5": DEFAULT_JUDGE_MODEL,
    "gpt5": DEFAULT_JUDGE_MODEL,
    "openai": DEFAULT_JUDGE_MODEL,
    "gemma": GEMMA_JUDGE_MODEL,
    "gemma-4": GEMMA_JUDGE_MODEL,
    "gemma-4-12b": GEMMA_JUDGE_MODEL,
    "gemma4-12b": GEMMA_JUDGE_MODEL,
    "open-source": GEMMA_JUDGE_MODEL,
    "opensource": GEMMA_JUDGE_MODEL,
}

#: Endpoint assumed for a locally served open-source judge; matches the default
#: port of ``startVLMmodel.sh``.
DEFAULT_JUDGE_BASE_URL = "http://localhost:8001/v1"


class JudgeConfig(NamedTuple):
    """Everything needed to reach a judge: which model, where, and with what key."""

    model: str
    base_url: Optional[str]
    api_key: str
    is_openai: bool


def _looks_like_openai(model: str) -> bool:
    """True for OpenAI-hosted families (GPT and the o-series reasoning models)."""
    name = model.lower()
    return name.startswith(("gpt-", "gpt3", "gpt4", "gpt5", "o1", "o3", "o4", "chatgpt"))


def resolve_judge(model: Optional[str] = None, base_url: Optional[str] = None) -> JudgeConfig:
    """Resolve the model id, endpoint and API key for the LLM judge.

    Model selection precedence: the explicit ``model`` argument, then the
    ``TW_JUDGE`` / ``TW_JUDGE_MODEL`` env var, then :data:`DEFAULT_JUDGE_MODEL`.
    Names are matched against :data:`JUDGE_ALIASES` case-insensitively, so
    ``"gemma"`` expands to :data:`GEMMA_JUDGE_MODEL`.

    A GPT / o-series id is routed to the OpenAI API and requires
    ``OPENAI_API_KEY`` (honouring ``OPENAI_BASE_URL`` for proxies). Any other id
    -- or any call that supplies an explicit ``base_url`` -- is treated as an
    open-source judge behind an OpenAI-compatible server: the endpoint comes from
    ``base_url``, then ``TW_JUDGE_BASE_URL`` / ``VLLM_API_URL``, then
    :data:`DEFAULT_JUDGE_BASE_URL`; the key from ``TW_JUDGE_API_KEY`` /
    ``VLLM_API_KEY``, defaulting to the throwaway ``"EMPTY"`` that vLLM accepts.
    """
    requested = model or os.environ.get("TW_JUDGE") or os.environ.get("TW_JUDGE_MODEL")
    requested = (requested or DEFAULT_JUDGE_MODEL).strip()
    resolved_model = JUDGE_ALIASES.get(requested.lower(), requested)

    explicit_base = base_url or os.environ.get("TW_JUDGE_BASE_URL")

    if explicit_base is None and _looks_like_openai(resolved_model):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                f"OPENAI_API_KEY environment variable not set (judge model {resolved_model!r}). "
                "Set it, or select the open-source judge with TW_JUDGE=gemma."
            )
        return JudgeConfig(
            model=resolved_model,
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=api_key,
            is_openai=True,
        )

    endpoint = explicit_base or os.environ.get("VLLM_API_URL") or DEFAULT_JUDGE_BASE_URL
    api_key = os.environ.get("TW_JUDGE_API_KEY") or os.environ.get("VLLM_API_KEY") or "EMPTY"
    return JudgeConfig(model=resolved_model, base_url=endpoint, api_key=api_key, is_openai=False)


def llm_fuzzy_match(
    pred: str,
    reference: str,
    question: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> float:
    """Check whether the prediction matches the reference using an LLM judge.

    ``model`` selects the judge (see :func:`resolve_judge`). ``None`` uses the
    ``TW_JUDGE`` env var or the paper's default GPT judge; pass ``"gemma"`` (or
    set ``TW_JUDGE=gemma``) to use the open-source alternate served locally.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package required for LLM judge evaluation. Install with: pip install openai"
        )

    judge = resolve_judge(model, base_url)
    client = OpenAI(api_key=judge.api_key, base_url=judge.base_url)

    message = f"""Help a teacher grade the answer of a student given a question. Keep in mind that the student may use different phrasing or wording to answer the question. The goal is to evaluate whether the answer is semantically equivalent to the reference answer.
Input:
- question: {question}
- reference answer: {reference}
- student answer: {pred}

Special Sequence: The string 'N/A' that you see is a special sequence that means 'not achievable'

Output: You must respond with EXACTLY one of the following words (nothing else):
1) 'correct': if the answer is semantically equivalent to the reference. 
   - Numeric values must match exactly (including units, signs, and scale) unless the question/reference clearly allows an approximation or rounding.
   - If an estimate is allowed, the student must still be reasonably close and not contradict the reference.
   - Ordered lists/steps/rankings must match exactly in both the element values and order.
   - Unordered lists/sets must contain the same element values; the order of the elements does not matter.
   - Extra information is allowed only if it does not introduce contradictions or change the meaning.
2) 'partially correct': if the answer is somewhat related but incomplete or inaccurate
3) 'incorrect': if the answer is wrong or unrelated
Do not include any additional text, explanation, or formatting. Only respond with one of the three words above."""

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": message},
    ]

    # API errors (rate limits, auth, network) must propagate — scoring them as
    # 0.0 would silently mark the episode as a failed task.
    response = client.chat.completions.create(
        model=judge.model,
        messages=messages,
        temperature=0,
        max_completion_tokens=768,
    )
    response_text = _normalize_openai_response_text(response).strip()
    raw_response = response_text  # Keep original for debugging

    logger.debug(f"LLM judge raw response: '{raw_response}'")
    # Also print in test mode (when called from test script)
    if os.environ.get("LLM_JUDGE_DEBUG", "").lower() in ("1", "true", "yes"):
        print(f"LLM Raw Response: '{raw_response}'")

    response_clean = response_text.lower().strip()

    # Check for exact matches first (most strict)
    if response_clean == "correct":
        return 1.0
    elif response_clean == "partially correct" or response_clean == "incorrect":
        return 0.0
    # Fallback to substring matching for robustness (in case LLM adds extra text).
    # Negative verdicts must be checked first: "incorrect" and "partially correct"
    # both contain "correct" as a substring.
    elif "incorrect" in response_clean or "partially correct" in response_clean:
        return 0.0
    elif "correct" in response_clean:
        logger.warning(
            f"LLM judge returned non-exact response: '{response_clean}'. Using fallback matching."
        )
        return 1.0
    else:
        # If response doesn't contain expected keywords, default to 0
        logger.warning(
            f"LLM judge returned unexpected response: '{response_clean}'. Defaulting to 0.0."
        )
        return 0.0


class LLMJudgeEvaluator(Evaluator):
    """LLM-based judge evaluator for semantic matching.

    ``model``/``base_url`` are resolved lazily by :func:`resolve_judge`, so
    leaving them ``None`` lets the ``TW_JUDGE`` env var (or the GPT default)
    decide which judge to use at scoring time.
    """

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.base_url = base_url

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page | None = None,
        client=None,
    ) -> float:
        with open(config_file, "r") as f:
            configs = json.load(f)

        last_action = self.get_last_action(trajectory)
        pred = last_action.get("answer", "")

        # Get the task goal/question from config
        question = configs.get("goal", configs.get("intent", ""))

        # Get reference answers from config
        ref_answers = configs["eval"].get("reference_answers", {})

        # Support both single reference and list of references
        if "fuzzy_match" in ref_answers:
            references = ref_answers["fuzzy_match"]
            if isinstance(references, str):
                references = [references]

            # Any reference can match (OR logic)
            for ref in references:
                if ref == "N/A":
                    # Special handling for N/A
                    if pred.strip().upper() == "N/A":
                        return 1.0
                else:
                    if llm_fuzzy_match(pred, ref, question, self.model, self.base_url) > 0:
                        return 1.0
            return 0.0

        return 0.0


class EvaluatorComb:
    """Combines multiple evaluators"""

    def __init__(self, evaluators: list[Evaluator]) -> None:
        self.evaluators = evaluators

    def __call__(
        self,
        trajectory: list,
        config_file: Path | str,
        page: Page,
        client=None,
    ) -> float:
        score = 1.0
        for evaluator in self.evaluators:
            score *= evaluator(trajectory, config_file, page, client)
        return score


#: Evaluator identifiers accepted in a task's ``eval.eval_types``. Everything
#: except ``llm_judge`` is deterministic.
SUPPORTED_EVAL_TYPES = (
    "string_match",
    "number_match",
    "list_match",
    "exact_match",
    "llm_judge",
)

DETERMINISTIC_EVAL_TYPES = tuple(t for t in SUPPORTED_EVAL_TYPES if t != "llm_judge")


def evaluator_router(config_file: Path | str) -> EvaluatorComb:
    """Route to appropriate evaluator based on config"""
    with open(config_file, "r") as f:
        configs = json.load(f)

    eval_types = configs["eval"]["eval_types"]
    evaluators: list[Evaluator] = []

    for eval_type in eval_types:
        match eval_type:
            case "exact_match":
                evaluators.append(ExactMatchEvaluator())
            case "string_match":
                evaluators.append(StringMatchEvaluator())
            case "number_match":
                evaluators.append(NumberMatchEvaluator())
            case "list_match":
                evaluators.append(ListMatchEvaluator())
            case "llm_judge":
                # A run-level TW_JUDGE env var (set for the alternate-judge run)
                # overrides a task's pinned llm_model, which overrides the GPT
                # default; resolve_judge fills in the default when both are unset.
                model = os.environ.get("TW_JUDGE") or configs["eval"].get("llm_model")
                base_url = os.environ.get("TW_JUDGE_BASE_URL") or configs["eval"].get(
                    "llm_base_url"
                )
                evaluators.append(LLMJudgeEvaluator(model=model, base_url=base_url))
            case _:
                raise ValueError(
                    f"eval_type {eval_type} is not supported. Supported types: "
                    f"{', '.join(SUPPORTED_EVAL_TYPES)}"
                )

    if not evaluators:
        raise ValueError("eval_types must list at least one evaluator")

    return EvaluatorComb(evaluators)
