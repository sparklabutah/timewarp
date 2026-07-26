# Deterministic verifier annotation

TimeWarp originally scored every task with an OpenAI LLM judge (`eval_types:
["llm_judge"]`). This directory holds the pipeline that replaced that judge with
deterministic verifiers for as many tasks as possible, keeping the judge only
where no deterministic spec can separate right from wrong.

The verifiers themselves live in the package, not here:

- [`src/browsergym/timewarp/normalization.py`](../../src/browsergym/timewarp/normalization.py)
  — stdlib-only text/number canonicalization and word-boundary matching
- [`src/browsergym/timewarp/evaluators.py`](../../src/browsergym/timewarp/evaluators.py)
  — `StringMatchEvaluator`, `NumberMatchEvaluator`, `ListMatchEvaluator`
- [`src/tests/timewarp/test_evaluators.py`](../../src/tests/timewarp/test_evaluators.py)
  — unit tests, including dataset-integrity checks

[`GUIDELINES.md`](GUIDELINES.md) is the annotation contract: verifier taxonomy,
selection table, and the traps that break naive specs.

## Pipeline

```
make_batches.py      231 tasks -> out/batches/batch_NN.json, stratified by
                     answer shape and site

  (annotation agents) draft a spec per task, plus 3 realistic correct answers
                      and 3 realistic wrong answers    -> out/drafts/
  (critic agents)     attack every spec with the oracle, repair, and finalize
                                                        -> out/annotations/

selfcheck_eval.py    the oracle. Executes specs; gates the merge
merge_eval_blocks.py merges into data/test.raw.v2.json, reports coverage,
                     writes REVIEW.md for the human-decision pile
env_lookup.py        queries the wiki/news/webshop content offline to spot-check
                     that a gold answer is actually correct
```

## The oracle

`selfcheck_eval.py` is what makes the annotations trustworthy — every spec is
executed rather than eyeballed.

```bash
# score one spec against one answer
python selfcheck_eval.py \
  --spec '{"eval_types":["string_match"],"reference_answers":{"must_include":["alaska"]}}' \
  --answer "The state is **Alaska**."

# run every check over an annotation file
python selfcheck_eval.py --input out/annotations/batch_03.json --verbose

# check the shipped dataset: every gold must satisfy its own verifier
python selfcheck_eval.py --dataset
```

Per annotation it checks that the task's own gold scores 1.0, that every
`positive_examples` entry scores 1.0, that every `negative_examples` entry
scores 0.0, and that the spec does not also accept a sample of *other* tasks'
gold answers (a spec that does is too lenient to discriminate).

## Merging

```bash
python merge_eval_blocks.py                 # build data/test.raw.v2.json + REVIEW.md
python merge_eval_blocks.py --validate-only # validate the shipped dataset
```

`test.raw.v2.json` and `REVIEW.md` are regenerable working artifacts and are not
checked in — the reviewed result is what ships in
[`data/test.raw.json`](../../src/browsergym/timewarp/data/test.raw.json). Rerun
the merge to reproduce them.

The merge preserves each task's original `fuzzy_match` gold inside
`reference_answers`. It is inert unless `llm_judge` is in `eval_types`, and it
keeps rescoring and rollback trivial. Each task also gains `revision` and an
`annotation` block recording confidence, notes and provenance.

## Spot-checking golds

Annotation works from the intent and the existing gold, so a wrong gold would
silently become a strict failure. `env_lookup.py` reads the environments'
content directly — much cheaper than booting the servers:

```bash
python env_lookup.py wiki --title "Borough" --grep Alaska
python env_lookup.py news --search Morocco --year 2009
python env_lookup.py shop --search "Type-C to HDMI"
```

Note the news index's `year` field is unreliable (most records carry the dump
year); `date` holds the real publication date, and `--year` filters on it.

Suspect golds are collected in the generated `REVIEW.md` (produced by the merge
above), never edited automatically.

## Comparing against the old judge

[`../analysis/rescore_compare.py`](../analysis/rescore_compare.py) scores
recorded episodes with both scorers and prints the disagreements to adjudicate:

```bash
python ../analysis/rescore_compare.py results/<model>/<version>_multiTest --judge --limit 50
```
