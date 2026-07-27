"""Unit tests for TimeWarp's deterministic verifiers.

Pure Python: no browser, no network, no API key. Every case builds a task
config in a temp file and scores a synthetic free-text answer through
``evaluator_router``, mirroring how ``GenericTimeWarpTask.validate`` calls it.
"""

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from browsergym.timewarp.evaluators import (
    DEFAULT_JUDGE_BASE_URL,
    DEFAULT_JUDGE_MODEL,
    DETERMINISTIC_EVAL_TYPES,
    GEMMA_JUDGE_MODEL,
    ListMatchEvaluator,
    NumberMatchEvaluator,
    StringMatchEvaluator,
    evaluator_router,
    resolve_judge,
)
from browsergym.timewarp.normalization import (
    extract_numbers,
    find_entry,
    first_sentence,
    normalize_text,
)

TASK_DATA = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "browsergym"
    / "timewarp"
    / "data"
    / "test.raw.json"
)


def score(eval_block: dict, answer: str, intent: str = "test intent") -> float:
    """Score ``answer`` against ``eval_block`` exactly as the task harness would."""
    config = {"task_id": 0, "intent": intent, "goal": intent, "eval": eval_block}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(config, handle)
        path = handle.name
    try:
        evaluator = evaluator_router(path)
        trajectory = [{}, {"action_type": "stop", "answer": answer}]
        return evaluator(trajectory=trajectory, config_file=path, page=None, client=None)
    finally:
        Path(path).unlink(missing_ok=True)


def string_eval(**references) -> dict:
    return {"eval_types": ["string_match"], "reference_answers": references}


def number_eval(scope: str = "full", **spec) -> dict:
    spec.setdefault("scope", scope)
    return {"eval_types": ["number_match"], "reference_answers": {"number_match": spec}}


def list_eval(**spec) -> dict:
    return {"eval_types": ["list_match"], "reference_answers": {"list_match": spec}}


# --------------------------------------------------------------------------- #
# Normalization primitives
# --------------------------------------------------------------------------- #


class TestNormalizeText:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("  Biology  ", "biology"),
            ('"Biology."', "biology"),
            ("**Biology**", "biology"),
            ("`Biology`", "biology"),
            ("Beyoncé", "beyonce"),
            ("Quest Lumaflex™ Band", "quest lumaflex band"),
            ("multi\n  line\ttext", "multi line text"),
            ("“smart quotes”", "smart quotes"),
            ("$9.99", "$9.99"),
            ("45%", "45%"),
            (None, ""),
        ],
    )
    def test_canonicalizes(self, raw, expected):
        assert normalize_text(raw) == expected

    def test_preserves_internal_punctuation(self):
        assert normalize_text("The U.S. government") == "the u.s. government"


class TestFirstSentence:
    def test_splits_on_terminator(self):
        assert first_sentence("Yes. It is mentioned in Biology.") == "Yes"

    def test_does_not_split_decimals(self):
        assert first_sentence("The price is 9.99 dollars") == "The price is 9.99 dollars"

    def test_splits_on_newline(self):
        assert first_sentence("No\nExplanation follows") == "No"

    def test_returns_whole_string_when_unsplittable(self):
        assert first_sentence("Biology") == "Biology"

    @pytest.mark.parametrize(
        "raw",
        ["**Yes.** There is no other article.", '"Yes." There is no other article.',
         "*Yes.* There is no other article.", "`Yes.` There is no other article."],
    )
    def test_splits_through_closing_markdown(self, raw):
        """Agents routinely bold the verdict; that must not swallow the whole answer."""
        assert normalize_text(first_sentence(raw)) == "yes"


class TestWordBoundaryContainment:
    @pytest.mark.parametrize(
        "answer, reference, matches",
        [
            ("The answer is 10", "10", True),
            ("The answer is 100", "10", False),
            ("It happened in 2010", "10", False),
            ("There are 10, not 11", "10", True),
            ("The article is in the north wing", "no", False),
            ("No, it is not listed", "no", True),
            ("It is not listed", "no", False),
            ("Send an e-mail", "e mail", True),
            ("Send an e mail", "e-mail", True),
            ("Hong Kong's population", "hong kong", True),
            ("**Biology** is the answer", "biology", True),
        ],
    )
    def test_boundaries(self, answer, reference, matches):
        assert (find_entry(answer, reference) is not None) is matches


class TestExtractNumbers:
    @pytest.mark.parametrize(
        "text, expected_subset",
        [
            ("$1,234.56", ["1234.56"]),
            ("It costs 9.99 dollars", ["9.99"]),
            ("Over 57.7 million people", ["57700000.0"]),
            ("around 7 million", ["7000000"]),
            ("7,000,000", ["7000000"]),
            ("Thirteen articles", ["13"]),
            ("twenty one", ["21"]),
            ("one hundred two", ["102"]),
            ("The 13th of May", ["13"]),
            ("45%", ["45"]),
            ("-5 degrees", ["-5"]),
            ("no numbers here", []),
        ],
    )
    def test_extraction(self, text, expected_subset):
        found = extract_numbers(text)
        for expected in expected_subset:
            assert any(value == Decimal(expected) for value in found), (text, found)
        if not expected_subset:
            assert found == []

    def test_ambiguous_suffix_yields_both_readings(self):
        found = extract_numbers("a 5m wingspan")
        assert Decimal(5) in found and Decimal(5_000_000) in found

    def test_metres_is_not_a_magnitude_suffix(self):
        found = extract_numbers("5 metres long")
        assert Decimal(5) in found and Decimal(5_000_000) not in found


# --------------------------------------------------------------------------- #
# StringMatchEvaluator
# --------------------------------------------------------------------------- #


class TestStringMatch:
    def test_exact_match_tolerates_formatting(self):
        block = string_eval(exact_match="Biology")
        assert score(block, "  **Biology.**  ") == 1.0
        assert score(block, "Chemistry") == 0.0

    def test_exact_match_rejects_verbose_answers(self):
        assert score(string_eval(exact_match="Biology"), "The answer is Biology") == 0.0

    def test_exact_match_list_is_any_of(self):
        block = string_eval(exact_match=["Biology", "Biological science"])
        assert score(block, "biological science") == 1.0

    def test_must_include_is_containment(self):
        block = string_eval(must_include=["biology"])
        assert score(block, "Biophysics is mentioned in the Biology article.") == 1.0
        assert score(block, "It appears only in Physics.") == 0.0

    def test_must_include_requires_all_entries(self):
        block = string_eval(must_include=["biology", "physics"])
        assert score(block, "Both Biology and Physics mention it.") == 1.0
        assert score(block, "Only Biology mentions it.") == 0.0

    def test_or_alternatives(self):
        block = string_eval(must_include=["kangaroos |OR| kangaroo"])
        assert score(block, "I found one kangaroo.") == 1.0
        assert score(block, "I found kangaroos.") == 1.0
        assert score(block, "I found wombats.") == 0.0

    def test_or_separator_tolerates_missing_spaces(self):
        """A spec written without the spaces must not silently match nothing."""
        block = string_eval(must_include=["kangaroos|OR|kangaroo"])
        assert score(block, "I found kangaroos.") == 1.0
        assert score(block, "I found wombats.") == 0.0

    def test_must_exclude(self):
        block = string_eval(must_include=["biology"], must_exclude=["both", "neither"])
        assert score(block, "It is mentioned in Biology only.") == 1.0
        assert score(block, "It is mentioned in both articles, Biology and Physics.") == 0.0

    def test_yes_no_with_first_sentence_scope(self):
        block = string_eval(
            must_include=["yes"], must_exclude=["no"], scope="first_sentence"
        )
        assert score(block, "Yes. There is no other article covering it.") == 1.0
        assert score(block, "**Yes.** There is no other article covering it.") == 1.0
        assert score(block, "No. The article does not exist.") == 0.0
        # "not" must not be read as the excluded token "no"
        assert score(block, "Yes, although it is not in the related pages list.") == 1.0
        # Without the scope the trailing "no" would sink a correct answer.
        unscoped = string_eval(must_include=["yes"], must_exclude=["no"])
        assert score(unscoped, "Yes. There is no other article covering it.") == 0.0

    def test_regex_entry(self):
        block = string_eval(must_include=["^yes.*$"], scope="first_sentence")
        assert score(block, "Yes, both articles mention it. Details follow.") == 1.0
        assert score(block, "No, neither does.") == 0.0

    def test_numeric_lookalike_is_rejected(self):
        block = string_eval(must_include=["10"])
        assert score(block, "There are 100 articles.") == 0.0
        assert score(block, "There are 10 articles.") == 1.0

    def test_empty_spec_raises(self):
        with pytest.raises(ValueError, match="at least one of"):
            score(string_eval(), "anything")

    def test_missing_reference_answers_raises(self):
        with pytest.raises(ValueError, match="reference_answers"):
            score({"eval_types": ["string_match"]}, "anything")


# --------------------------------------------------------------------------- #
# NumberMatchEvaluator
# --------------------------------------------------------------------------- #


class TestNumberMatch:
    def test_formatting_independence(self):
        block = number_eval(value=7000000)
        for answer in ["7,000,000", "7000000", "7 million", "The difference is 7 million people."]:
            assert score(block, answer) == 1.0, answer
        assert score(block, "70 million") == 0.0

    def test_relative_tolerance_for_hedged_golds(self):
        block = number_eval(value=7000000, rel_tolerance=0.1)
        assert score(block, "around 7.2 million") == 1.0
        assert score(block, "about 9 million") == 0.0

    def test_currency(self):
        block = number_eval(value=9.99, abs_tolerance=0.01)
        assert score(block, "It costs $9.99") == 1.0
        assert score(block, "9.99 dollars") == 1.0
        assert score(block, "It costs $99.90") == 0.0

    def test_spelled_out_numbers(self):
        assert score(number_eval(value=13), "Thirteen articles are listed.") == 1.0
        assert score(number_eval(value=13), "13 articles are listed.") == 1.0

    def test_exact_by_default(self):
        assert score(number_eval(value=2010), "It was founded in 2011.") == 0.0

    def test_multiple_required_values(self):
        block = number_eval(values=[5, 1.8])
        assert score(block, "The wingspan is 5 metres and the height 1.8 metres.") == 1.0
        assert score(block, "The wingspan is 5 metres.") == 0.0

    def test_no_numbers_in_answer(self):
        assert score(number_eval(value=13), "I could not find it.") == 0.0

    def test_missing_value_raises(self):
        with pytest.raises(ValueError, match="'value' or 'values'"):
            score(number_eval(), "13")


# --------------------------------------------------------------------------- #
# ListMatchEvaluator
# --------------------------------------------------------------------------- #


class TestListMatch:
    ANIMALS = [["koalas |OR| koala"], ["kangaroos |OR| kangaroo"], ["wombats |OR| wombat"]]

    def test_unordered_requires_every_item(self):
        block = list_eval(items=self.ANIMALS)
        assert score(block, "Wombats, koalas and kangaroos live there.") == 1.0
        assert score(block, "Koalas and kangaroos live there.") == 0.0

    def test_extra_items_are_tolerated(self):
        block = list_eval(items=self.ANIMALS)
        assert score(block, "Koalas, kangaroos, wombats, numbats and platypus.") == 1.0

    def test_ordered_enforces_sequence(self):
        block = list_eval(items=[["periodic table"], ["atomic number"], ["proton"]], ordered=True)
        assert score(block, "Periodic table, then atomic number, then proton.") == 1.0
        assert score(block, "Proton, then atomic number, then periodic table.") == 0.0

    def test_unordered_ignores_sequence(self):
        block = list_eval(items=[["periodic table"], ["atomic number"]], ordered=False)
        assert score(block, "Atomic number comes from the periodic table.") == 1.0

    def test_forbidden_entries(self):
        block = list_eval(items=[["koalas"]], forbidden=["dingoes"])
        assert score(block, "Koalas.") == 1.0
        assert score(block, "Koalas and dingoes.") == 0.0

    def test_plain_string_items(self):
        assert score(list_eval(items=["koalas", "wombats"]), "Koalas and wombats.") == 1.0

    def test_empty_items_raises(self):
        with pytest.raises(ValueError, match="non-empty 'items'"):
            score(list_eval(items=[]), "anything")


# --------------------------------------------------------------------------- #
# Router and combination semantics
# --------------------------------------------------------------------------- #


class TestRouter:
    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="not supported"):
            score({"eval_types": ["program_html"], "reference_answers": {}}, "x")

    def test_empty_eval_types_raises(self):
        with pytest.raises(ValueError, match="at least one evaluator"):
            score({"eval_types": [], "reference_answers": {}}, "x")

    def test_combined_types_are_anded(self):
        block = {
            "eval_types": ["string_match", "number_match"],
            "reference_answers": {
                "must_include": ["food and drug administration"],
                "number_match": {"value": 1906},
            },
        }
        assert score(block, "The Food and Drug Administration was formed in 1906.") == 1.0
        assert score(block, "The Food and Drug Administration was formed in 1907.") == 0.0
        assert score(block, "The agency was formed in 1906.") == 0.0

    def test_deterministic_type_list_excludes_llm_judge(self):
        assert "llm_judge" not in DETERMINISTIC_EVAL_TYPES
        assert set(DETERMINISTIC_EVAL_TYPES) >= {"string_match", "number_match", "list_match"}


# --------------------------------------------------------------------------- #
# Dataset integrity
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# LLM judge selection (offline: resolve_judge does no network I/O)
# --------------------------------------------------------------------------- #


JUDGE_ENV_VARS = (
    "TW_JUDGE",
    "TW_JUDGE_MODEL",
    "TW_JUDGE_BASE_URL",
    "TW_JUDGE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "VLLM_API_URL",
    "VLLM_API_KEY",
)


@pytest.fixture
def clean_judge_env(monkeypatch):
    """Start every judge-selection test from an empty, deterministic environment."""
    for name in JUDGE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


class TestJudgeSelection:
    def test_default_is_the_gpt_paper_judge(self, clean_judge_env):
        clean_judge_env.setenv("OPENAI_API_KEY", "sk-test")
        judge = resolve_judge()
        assert judge.model == DEFAULT_JUDGE_MODEL
        assert judge.is_openai is True
        assert judge.base_url is None
        assert judge.api_key == "sk-test"

    def test_gpt_judge_requires_api_key(self, clean_judge_env):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            resolve_judge()

    def test_openai_base_url_is_honoured_for_proxies(self, clean_judge_env):
        clean_judge_env.setenv("OPENAI_API_KEY", "sk-test")
        clean_judge_env.setenv("OPENAI_BASE_URL", "https://proxy.example/v1")
        assert resolve_judge().base_url == "https://proxy.example/v1"

    def test_gemma_alias_routes_to_local_open_source_server(self, clean_judge_env):
        """No OPENAI_API_KEY needed; the alternate judge is self-hosted."""
        judge = resolve_judge("gemma")
        assert judge.model == GEMMA_JUDGE_MODEL
        assert judge.is_openai is False
        assert judge.base_url == DEFAULT_JUDGE_BASE_URL
        assert judge.api_key == "EMPTY"

    def test_tw_judge_env_selects_the_alternate(self, clean_judge_env):
        clean_judge_env.setenv("TW_JUDGE", "gemma-4-12b")
        judge = resolve_judge()
        assert judge.model == GEMMA_JUDGE_MODEL
        assert judge.is_openai is False

    def test_explicit_argument_beats_env(self, clean_judge_env):
        clean_judge_env.setenv("TW_JUDGE", "gemma")
        clean_judge_env.setenv("OPENAI_API_KEY", "sk-test")
        assert resolve_judge("gpt-5").model == DEFAULT_JUDGE_MODEL

    def test_vllm_env_configures_the_open_source_endpoint(self, clean_judge_env):
        clean_judge_env.setenv("VLLM_API_URL", "http://gpu-node:9000/v1")
        clean_judge_env.setenv("VLLM_API_KEY", "secret")
        judge = resolve_judge("gemma")
        assert judge.base_url == "http://gpu-node:9000/v1"
        assert judge.api_key == "secret"

    def test_tw_judge_base_url_overrides_vllm_url(self, clean_judge_env):
        clean_judge_env.setenv("VLLM_API_URL", "http://gpu-node:9000/v1")
        clean_judge_env.setenv("TW_JUDGE_BASE_URL", "http://localhost:1234/v1")
        assert resolve_judge("gemma").base_url == "http://localhost:1234/v1"

    def test_base_url_forces_open_source_route_for_a_gpt_name(self, clean_judge_env):
        """Pointing at a local endpoint must not demand an OpenAI key."""
        judge = resolve_judge(model="gpt-5", base_url="http://localhost:8001/v1")
        assert judge.is_openai is False
        assert judge.api_key == "EMPTY"

    def test_unknown_model_id_is_passed_through_verbatim(self, clean_judge_env):
        judge = resolve_judge("Qwen/Qwen2.5-7B-Instruct")
        assert judge.model == "Qwen/Qwen2.5-7B-Instruct"
        assert judge.is_openai is False


class TestDataset:
    @staticmethod
    def load():
        return json.loads(TASK_DATA.read_text())

    def test_every_task_builds_an_evaluator(self):
        """Guards against a bad annotation merge landing in the shipped dataset."""
        for task in self.load():
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
                json.dump(task, handle)
                path = handle.name
            try:
                combination = evaluator_router(path)
                assert combination.evaluators, task["task_id"]
            finally:
                Path(path).unlink(missing_ok=True)

    def test_every_task_keeps_a_fuzzy_match_gold(self):
        """The original gold stays in place so runs remain A/B comparable."""
        for task in self.load():
            references = task["eval"].get("reference_answers", {})
            assert "fuzzy_match" in references, task["task_id"]

    def test_deterministic_specs_are_well_formed(self):
        for task in self.load():
            references = task["eval"].get("reference_answers", {})
            for eval_type in task["eval"]["eval_types"]:
                if eval_type == "number_match":
                    spec = references["number_match"]
                    assert "value" in spec or "values" in spec, task["task_id"]
                elif eval_type == "list_match":
                    assert references["list_match"].get("items"), task["task_id"]
                elif eval_type == "string_match":
                    assert any(
                        key in references
                        for key in ("exact_match", "must_include", "must_exclude")
                    ), task["task_id"]
