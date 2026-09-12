# Lean 4 formalization of the TimeWarp theory

Machine-checked proofs of the mathematical content of the TimeWarp paper: Appendix
§"A Theoretical Perspective on Multi-Version Training" (`sec:theory`) in full — the Setting,
Assumption `ass:bounded`, Definition `def:discrepancy`, Proposition `prop:versionCount` with
Eqs. `eq:versionCountBound`/`eq:excessRisk`, Proposition `prop:coverage` with
Eq. `eq:coverageBound`, and the checkable predictions of Remarks `rem:versionCountBridge` and
`rem:coverageBridge` — plus the relation between the two behaviour-cloning losses of
Eqs. `eq:vanillaBCLoss` and `eq:timewarpBC`.

Every file compiles against Mathlib with no `sorry` and no new axioms. The only axioms used
are Lean's three standard ones: `propext`, `Classical.choice` and `Quot.sound`
(`scripts/Audit.lean` prints this for all 32 headline results).

**Hoeffding's inequality is not assumed.** The paper cites it; here it is derived from
Mathlib's `hasSubgaussianMGF_of_mem_Icc` (Hoeffding's lemma) and
`HasSubgaussianMGF.measure_sum_ge_le_of_iIndepFun`, so Proposition `prop:versionCount` is
proved from first principles rather than from a quoted black box.

## Building

Lean (via `elan`) lives in `~/.elan`; the shell profile was not edited.

```sh
cd proofs
~/.elan/bin/lake exe cache get   # only on a fresh clone (downloads prebuilt Mathlib)
~/.elan/bin/lake build           # checks every proof
```

Toolchain: Lean `v4.34.0-rc2`, Mathlib `v4.34.0-rc2` (pinned in `lakefile.toml`).
`.lake/` holds the Mathlib build cache (several GB) and is git-ignored.

## Files

| File | Paper content |
|---|---|
| `TimeWarp/Discrepancy.lean` | Definition `def:discrepancy` (Eq. `eq:discrepancy`) and the three properties claimed after it; `disc ≤ B` from Assumption `ass:bounded` |
| `TimeWarp/Coverage.lean` | Proposition `prop:coverage` (Eq. `eq:coverageBound`), its monotonicity claim, and two counterexamples to the printed statement |
| `TimeWarp/Hoeffding.lean` | Hoeffding's inequality for the mean of independent `[0,B]` variables, both directions, plus the `ε = B √(log(1/η)/(2n))` calibration |
| `TimeWarp/Sampling.lean` | The Setting: `𝒫`, `𝒟_{τ,v}`, Eqs. `eq:versionRisk`, `eq:freshRisk`, `eq:pooledRisk`; the sampling model; the "Across versions" and "Within versions" steps |
| `TimeWarp/VersionCount.lean` | Proposition `prop:versionCount`: `ε₁`, `ε₂`, their calibration to `δ/(4\|Θ\|)`, the "Union bound" and "Excess risk" steps, Eqs. `eq:versionCountBound` and `eq:excessRisk` |
| `TimeWarp/Remarks.lean` | The two predictions of Remark `rem:versionCountBridge` |
| `TimeWarp/Bridge.lean` | The corrected bridge from Eq. `eq:coverageBound` to the pooled *empirical* objective, and the set-vs-sequence issue in Eq. `eq:pooledRisk` |
| `TimeWarp/Losses.lean` | Eq. `eq:vanillaBCLoss` vs Eq. `eq:timewarpBC`: `L_BC ≤ L_TW-BC`, with equality iff degenerate |

## Paper statement → Lean theorem

Namespace `TimeWarp` throughout. `V` indexes versions, `Z` is the space of history-response
pairs `(h,y)`, `Θ` the policy class, `ℓ θ z` the per-sample loss, `B` its bound.

| Paper | Lean |
|---|---|
| Assumption `ass:bounded` | `LossBound` (`0 < B`, `ℓ` measurable, `ℓ ∈ [0,B]`) together with `[Finite Θ]` |
| Eq. `eq:discrepancy` | `disc` |
| "symmetric, vanishes for `u = v`, satisfies the triangle inequality" | `disc_comm`, `disc_self`, `disc_triangle` |
| `disc ≤ B` under Assumption `ass:bounded` | `disc_le_of_mem_Icc` |
| Eq. `eq:versionRisk` (`L_v`) | `riskV` |
| Eq. `eq:freshRisk` (`L_𝒫`) | `riskP` |
| `\bar L_tr` (average population risk over drawn versions) | `riskBar` |
| Eq. `eq:pooledRisk` (`\hat L_tr`) | `riskHat` |
| The two-stage experiment (versions, then pairs) | `versMeasure`, `seedMeasure`, `sampleMeasure` |
| Proof step "Across versions" | `across_versions`, `across_versions_rev` |
| Proof step "Within versions" | `within_versions`, `within_versions_rev` |
| "The right-hand side does not depend on `𝒱_tr`" | `sampleMeasure_real_le_of_slice` |
| `ε₁`, `ε₂` | `eps1`, `eps2` |
| "each one-sided event has probability at most `δ/(4\|Θ\|)`" | `exp_eps1`, `exp_eps2` |
| Proof step "Union bound" | `real_badEvent_le` (via `badEvent`) |
| Eqs. `eq:versionCountBound` + `eq:excessRisk` | `versionCount` (third and fourth conclusions) |
| Remark `rem:versionCountBridge` (i) | `eps1_one`, `eps1_pos`, `single_version_floor` |
| Remark `rem:versionCountBridge` (ii) | `eps2_of_budget`, `eps1_antitone`, `fixed_budget` |
| Prop. `prop:coverage`, first inequality | `coverage_le_min` |
| Prop. `prop:coverage`, second inequality | `coverage_le_average` (via `inf'_le_average`) |
| Prop. `prop:coverage`, both | `coverage` |
| "non-increasing in `𝒱_tr` with respect to set inclusion" | `coverage_min_antitone` |
| "adding one close to `u` tightens it most" (Remark `rem:coverageBridge`: discrepancy zero) | `coverage_min_eq_of_mem` |
| Eq. `eq:coverageBound` for the drawn sequence | `coverage_seq` |
| Eq. `eq:vanillaBCLoss` vs Eq. `eq:timewarpBC` | `prob_le_actionProb`, `bcLoss_le_twbcLoss`, `prob_eq_actionProb_iff` |

## Modelling choices

* **The probability space.** Proposition `prop:versionCount` draws `k` versions i.i.d. from
  `𝒫` and then, given the versions, `M` pairs per version from `𝒟_{τ,v}`. Rather than build a
  Markov kernel, `Sampling.lean` draws, for each of the `k·M` sample slots, *one pair per
  version* from `⨂_v 𝒟_{τ,v}` and reads off the coordinate of the version actually drawn. The
  read-off coordinate has law `𝒟_{τ,v}` and the slots are independent, so this is the same
  experiment, written as a plain product measure. The conditioning step of the proof then
  becomes Fubini (`Measure.prod_apply`).
* **Versions.** `V` is a finite type with the discrete σ-algebra, matching `𝒱 = {1,…,n}`.
* **Policy class.** `[Finite Θ]` is the second half of Assumption `ass:bounded`. Nonemptiness,
  which the paper leaves implicit (it writes `min_{θ∈Θ}` and `argmin`), is stated as
  `[Nonempty Θ]`.
* **Independence of pairs.** As the Setting says, "Treating the pairs as independent ignores
  the dependence between steps of one trajectory". The formalization takes the same
  simplification: pairs are the unit of data.
* **Not formalized:** the empirical predictions of the two remarks (which table or figure the
  bound is consistent with), the `[THEORY-TODO]` citation list, and everything outside
  `sec:theory` that is not a mathematical statement.

## Discrepancies found while formalizing

Proposition `prop:versionCount` and its proof are **correct as printed**: the two Hoeffding
applications, the calibration `exp(-2kε₁²/B²) = δ/(4|Θ|)` and `exp(-2kMε₂²/B²) = δ/(4|Θ|)`,
the `δ/2 + δ/(2|Θ|) ≤ δ` union-bound accounting, and the excess-risk chain all check out
(`versionCount`). The findings below are about the surrounding statements.

1. **Eq. `eq:timewarpBC` is not a "reformulation" of Eq. `eq:vanillaBCLoss`.**
   §`sec:timewarpBC` writes "The standard BC loss (Eq. `eq:vanillaBCLoss`) can be reformulated
   as" and then gives the full-response loss. The action probability is the marginal of the
   response probability over the parser's fibre, so `π_θ(a|h) ≥ π_θ(y|h)` and therefore
   `L_BC(θ) ≤ L_TW-BC(θ)`, with equality only when no other response shares the action
   (`prob_le_actionProb`, `bcLoss_le_twbcLoss`, `prob_eq_actionProb_iff`). Two responses
   sharing one action with half the mass each give `0 < log 2`
   (`bcLoss_lt_twbcLoss_example`). The two are different objectives, which is exactly what
   the same paragraph claims as the contribution ("we train web agents on the full
   teacher-agent response rather than only on action tokens"). Suggested fix: "can be replaced
   by" / "we instead minimize".

2. **Proposition `prop:coverage` needs `𝒱_tr ≠ ∅`.** It is stated for "every set of training
   versions `𝒱_tr`", and the right-most expression of Eq. `eq:coverageBound` divides by
   `k = |𝒱_tr|`. For `𝒱_tr = ∅` the bound reads `0` and the inequality is false
   (`coverage_empty_false`). The middle expression is also undefined (a minimum over an empty
   set). Suggested fix: add "nonempty".

3. **The takeaway after Proposition `prop:coverage` names the wrong objective.** It says the
   right-most expression bounds the loss "by the pooled objective that TimeWarp-BC minimizes
   plus the average discrepancy". The right-most expression is `(1/k) Σ_v L_v(θ)`, the average
   *population* risk; the pooled objective TimeWarp-BC minimizes is `\hat L_tr(θ)` of
   Eq. `eq:pooledRisk`, which is *empirical*. Passing from one to the other costs a
   concentration term: `L_u(θ) ≤ \hat L_tr(θ) + ε + (1/k) Σ_i disc(u, v_i)` on an event of
   probability at least `1 - exp(-2kMε²/B²)` (`coverage_pooled_le`, using `within_versions`).
   Suggested fix: either say "average population risk on the training versions", or state the
   empirical version with the extra term.

4. **Readability: monotonicity holds for the middle expression only.** The proposition scopes
   this correctly ("The middle expression is non-increasing in `𝒱_tr`"), and the takeaway's
   "adding a training version can only tighten the bound" sits in the sentence about the
   closest training version. But the next sentence moves to the right-most expression without
   re-scoping, and that bound is *not* monotone: with `L(v₁) = 0`, `L(v₂) = 10` and `u = v₁`
   it rises from `0` to `10` when `v₂` is added (`coverage_average_not_antitone`). Worth one
   clarifying clause.

5. **Eq. `eq:pooledRisk` sums over a set, but the versions are drawn i.i.d.** The Setting
   writes `𝒱_tr ⊆ 𝒱` with `|𝒱_tr| = k` and sums over `v ∈ 𝒱_tr`, while Proposition
   `prop:versionCount` draws the `k` versions i.i.d. from `𝒫`. Independent draws can coincide,
   in which case the set has fewer than `k` elements and the set-indexed sum has fewer than
   `kM` terms, so it is not the average the proof concentrates
   (`pooled_set_ne_pooled_seq`). Suggested fix: index the training versions as a sequence
   `v₁,…,v_k` (as this formalization does), or say "with repetition".

6. **Unit mismatch in Remark `rem:versionCountBridge`(ii).** It speaks of "a fixed budget of
   `kM` trajectories", but the Setting fixes the unit of data as history-response pairs
   ("`𝒱_tr` … contributes `M` history-response pairs per version"; "The analysis treats
   history-response pairs as the unit of data"). The prediction itself is correct
   (`fixed_budget`); only the noun is wrong.

7. **Presentational: "Consequently" in Proposition `prop:versionCount`.** Eq. `eq:excessRisk`
   does not follow from Eq. `eq:versionCountBound` alone — it also needs the two
   lower-deviation events at the fixed minimizer `θ*`. The proof does include them in the
   union bound, so "with the same probability" is accurate; but "Consequently" suggests the
   weaker derivation. The formal statement (`versionCount`) exposes this by carrying both
   conclusions on one explicitly-constructed event.
