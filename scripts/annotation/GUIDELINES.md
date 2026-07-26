# TimeWarp verifier annotation guidelines

Every TimeWarp task is currently scored by an LLM judge. We are replacing that
with deterministic verifiers. Your job: given a task's `intent`, optional
`additional_instructions`, and its existing gold answer (`fuzzy_match`), write
the strictest verifier spec that still accepts every *genuinely correct* answer.

**Use `llm_judge` sparingly.** It is the fallback of last resort, not a
convenience. A task only stays on `llm_judge` if no combination of the verifiers
below can separate correct from incorrect answers.

## What the agent's answer looks like

The agent replies in free text through `send_msg_to_user`. Assume the answer is
a *sentence*, not a bare value, and that it may:

- restate the question ("The country that uses boroughs is **Alaska**.")
- use markdown (`**Alaska**`, `` `Alaska` ``), quotes, or trailing periods
- add justification after the answer ("Yes. The article does not list it under
  related pages, but biophysics appears in the branches section.")
- format numbers differently from the gold ("7 million" vs "7,000,000")

Normalization already handles case, unicode/accents, markdown emphasis,
surrounding punctuation, and whitespace. You do **not** need to enumerate those
variants. You *do* need to handle genuine wording alternatives.

## Verifier taxonomy

Specs live in `eval.reference_answers`. Declare which verifiers run in
`eval_types`; multiple verifiers are combined with AND.

### `string_match` — the default

```json
{"eval_types": ["string_match"],
 "reference_answers": {
   "must_include": ["alaska"],
   "must_exclude": [],
   "scope": "full"
 }}
```

| Key | Meaning |
|---|---|
| `must_include` | Every entry must appear in the answer. Matching is on word boundaries, so `"10"` never matches `"100"` and `"no"` never matches `"north"`. |
| `must_exclude` | No entry may appear. |
| `exact_match` | The whole (normalized) answer must equal one of these. Almost never usable — a verbose answer fails it. |
| `scope` | `"full"` (default) or `"first_sentence"` — restricts matching to the leading sentence. |

An entry may offer alternatives with `" |OR| "`:
`"kangaroos |OR| kangaroo"`. An entry written as `^...$` is a regex matched
against the whole normalized (scoped) text.

### `number_match` — quantities, prices, measurements

```json
{"eval_types": ["number_match"],
 "reference_answers": {"number_match": {"value": 7000000, "rel_tolerance": 0.1}}}
```

Parses every number out of the answer and requires the expected value among
them. Handles `1,234.56`, `$9.99`, `57.7 million`, `13th`, and spelled-out
cardinals (`thirteen` → 13). Use `values: [...]` when several numbers are
required. Comparison is **exact unless you give a tolerance**:

- exact (no tolerance): counts, years, IDs
- `abs_tolerance: 0.01`: currency
- `rel_tolerance`: only for a gold that is itself hedged ("Around 7 million",
  "Over 57.7 million") — set it to the hedge's real slack, e.g. `0.1`

### `list_match` — enumerations

```json
{"eval_types": ["list_match"],
 "reference_answers": {"list_match": {
   "items": [["germany"], ["italy"], ["luxembourg"], ["netherlands"], ["spain"]],
   "ordered": true,
   "forbidden": []
 }}}
```

Each item is a list of interchangeable spellings; all items must appear.
Set `ordered: true` **only when the task itself demands an order** ("in
alphabetical order", "trace this path in the exact order", rankings) — it then
requires the items' first occurrences to appear in that order. `forbidden`
entries must not appear.

## Choosing a verifier

| Gold looks like | Use |
|---|---|
| Yes / No (possibly with a tail: "No, it does not.") | `string_match`, `scope: "first_sentence"`, `must_include: ["no"]`, `must_exclude: ["yes"]` |
| A named entity, title, or phrase ("Alaska", "Generic Tamiflu in India") | `string_match` with `must_include` |
| A year, ID, or code ("1903") | `string_match` with `must_include` — literal digits, no magnitude ambiguity |
| A count, price, distance, population ("$9.99", "Around 7 million") | `number_match` |
| A number written as a word ("One", "Thirteen") | `number_match` (it parses both spellings) |
| Several values that must all be present ("Germany, Italy, ...") | `list_match` |
| A choice between options named in the intent | see the trap below |
| A free-form sentence with no checkable anchor | `llm_judge` — but look hard for an anchor first |

## Traps — read before writing any spec

**1. The wrong option is named in the intent.** Tasks like *"Which cable is
longer: the white Type-C to HDMI Cable or the Type-C USB Charger Cable?"*
(gold: `White Type-C to HDMI Cable`) are the most common source of a broken
spec. A wrong answer will happily contain the gold string: *"The Type-C USB
Charger Cable is longer than the white Type-C to HDMI Cable."*

Fix: set `scope: "first_sentence"`, `must_include` the token that is unique to
the **correct** option, and `must_exclude` the token unique to the **wrong**
option:

```json
{"must_include": ["hdmi"], "must_exclude": ["usb charger"], "scope": "first_sentence"}
```

Always check whether the gold string (or a distractor) appears in the intent or
`additional_instructions`. If it does, plain `must_include` on the full answer
is compromised.

**2. `must_exclude` on explanatory answers.** A correct answer often mentions
what it ruled out: *"Biophysics appears in Biology, not in Physics."* Excluding
`"physics"` there would reject a correct answer. Only exclude tokens that
**cannot** occur in any correct answer — typically the literal choice words
`"both"` / `"neither"`, or a competing option's distinctive token under
`scope: "first_sentence"`.

**3. Low-discriminative golds.** A gold like `"people"` or `"One"` is a word
that can appear incidentally anywhere in a sentence. The spec will still be
right most of the time, but mark `confidence: "medium"` and make sure your
negative examples probe the incidental-occurrence case.

**4. Multiple-choice with "both"/"neither".** *"...in the Biology article, the
Physics article, both, or neither?"* with gold `Biology`:
`must_include: ["biology"]`, `must_exclude: ["both", "neither"]`. Do not exclude
`"physics"`.

**5. Ordered lists.** Only set `ordered: true` if the intent asks for an order.
Pick items whose first occurrence in prose reflects their real position — avoid
items whose token is likely to appear early in a preamble.

**6. Don't over-fit to the gold's phrasing.** Gold `"Found negative news."` →
`must_include: ["found negative news"]`, not `exact_match`. Gold
`"No, it does not."` → yes/no rule, not the full sentence.

## Confidence and the escape hatch

- `confidence: "high"` — the spec cannot plausibly accept a wrong answer or
  reject a right one.
- `confidence: "medium"` — a low-discriminative gold, or a `must_exclude` you
  had to reason about.
- `confidence: "low"` — you are unsure; explain in `notes`. Still write your
  best deterministic spec.
- `subjective: true` — **only** when no deterministic spec can work. Set
  `eval_types: ["llm_judge"]` and leave `reference_answers` empty. Justify it in
  `notes`. Expect this to be rare.

Also set `gold_suspect: true` (with a note) if the gold answer looks wrong or
does not answer the intent. Do not "fix" it — it goes to human review.

## Required examples

Every annotation must ship its own test cases. These are executed against your
spec; if a negative example passes, your spec is too lenient and comes back to
you for repair.

- `positive_examples` — 3 realistic **correct** answers in different styles: a
  terse one, a verbose one with justification, and one with markdown or an
  alternative phrasing/number format.
- `negative_examples` — 3 realistic **wrong** answers. At least one must be the
  hardest near-miss you can think of: the wrong option from the intent, an
  off-by-one number, or a wrong answer that quotes the gold token from the
  question.

Do not write joke examples ("banana"). They must be answers a competent agent
could actually produce.
