/-
Two places where the appendix's prose about Eq. `eq:coverageBound` and Eq. `eq:pooledRisk`
says slightly more than the formulas do, each with the corrected statement.

1. The takeaway after Proposition `prop:coverage` reads "The right-most expression bounds the
   same quantity by the pooled objective that \timewarp-BC minimizes plus the average
   discrepancy to the training versions." The right-most expression of Eq. `eq:coverageBound`
   is `(1/k) Σ_v L_v(θ)`, the average *population* risk `\bar L_tr(θ)`. The pooled objective
   \timewarp-BC minimises is `\hat L_tr(θ)` of Eq. `eq:pooledRisk`, which is *empirical*.
   Passing from one to the other costs the within-version concentration term
   (`coverage_pooled_le`).

2. The Setting writes the training versions as a set `𝒱_tr ⊆ 𝒱` with `|𝒱_tr| = k` and sums
   over `v ∈ 𝒱_tr` in Eq. `eq:pooledRisk`, while Proposition `prop:versionCount` draws the `k`
   training versions i.i.d. from `𝒫`. Independent draws can repeat, so they form a multiset of
   size `k` whose underlying set can be smaller, and the set-indexed sum then has fewer than
   `kM` terms (`pooled_set_ne_pooled_seq`).
-/
import TimeWarp.Sampling
import TimeWarp.Discrepancy

set_option linter.unusedSectionVars false

namespace TimeWarp

open MeasureTheory

variable {V Z Θ : Type*}
variable [Fintype V] [MeasurableSpace V] [DiscreteMeasurableSpace V] [MeasurableSpace Z]
variable {ℓ : Θ → Z → ℝ} {B : ℝ} {D : V → Measure Z} [∀ v, IsProbabilityMeasure (D v)]
variable {k M : ℕ} [Finite Θ] [Nonempty Θ]

/-- Eq. `eq:coverageBound` written for the drawn sequence of versions rather than for a set:
`L_u(θ) ≤ \bar L_tr(θ) + (1/k) Σ_i disc_Θ(u, v_i)`. This is the form that matches the sampling
model of Proposition `prop:versionCount`. -/
theorem coverage_seq (θ : Θ) (u : V) (vs : Vers V k) (hk : 0 < k) :
    riskV D ℓ u θ
      ≤ riskBar D ℓ k vs θ + (∑ i, disc (fun v θ' => riskV D ℓ v θ') u (vs i)) / k := by
  have hk0 : (0:ℝ) < k := by exact_mod_cast hk
  have hpt : ∀ i : Fin k, riskV D ℓ u θ
      ≤ riskV D ℓ (vs i) θ + disc (fun v θ' => riskV D ℓ v θ') u (vs i) := by
    intro i
    have := sub_le_disc (fun v θ' => riskV D ℓ v θ') u (vs i) θ
    linarith
  have hsum : (k:ℝ) * riskV D ℓ u θ
      ≤ ∑ i, (riskV D ℓ (vs i) θ + disc (fun v θ' => riskV D ℓ v θ') u (vs i)) := by
    calc (k:ℝ) * riskV D ℓ u θ = ∑ _i : Fin k, riskV D ℓ u θ := by
          rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
      _ ≤ _ := Finset.sum_le_sum fun i _ => hpt i
  rw [Finset.sum_add_distrib] at hsum
  rw [riskBar, ← add_div, le_div_iff₀ hk0, mul_comm]
  exact hsum

/-- **Corrected bridge to the pooled objective.** On a run where the within-version deviation
is below `ε` -- an event of probability at least `1 - exp(-2kMε²/B²)` by `within_versions` --
the loss on an unseen version `u` is bounded by the *empirical* pooled objective
`\hat L_tr(θ)` of Eq. `eq:pooledRisk` plus `ε` plus the average discrepancy. The extra `ε` is
what the takeaway after Proposition `prop:coverage` leaves out. -/
theorem coverage_pooled_le (θ : Θ) (u : V) (ω : Sample V Z k M) (hk : 0 < k) {ε : ℝ}
    (hgood : riskBar D ℓ k ω.1 θ - riskHat ℓ k M ω θ < ε) :
    riskV D ℓ u θ
      ≤ riskHat ℓ k M ω θ + ε + (∑ i, disc (fun v θ' => riskV D ℓ v θ') u (ω.1 i)) / k := by
  have h := coverage_seq (D := D) (ℓ := ℓ) θ u ω.1 hk
  linarith

/-- **The set-indexed sum of Eq. `eq:pooledRisk` is not the sum over the `k` draws.** Two
i.i.d. draws can coincide; the set `𝒱_tr` then has one element and the sum of Eq.
`eq:pooledRisk` has `M` terms rather than `kM`, so it is not the quantity the proof of
Proposition `prop:versionCount` concentrates. Indexing the training versions as a sequence
`v_1, …, v_k` (as this development does) removes the ambiguity. -/
theorem pooled_set_ne_pooled_seq :
    ∃ (vs : Fin 2 → Bool) (f : Bool → ℝ),
      (∑ v ∈ Finset.image vs Finset.univ, f v) ≠ ∑ i, f (vs i) := by
  refine ⟨fun _ => true, fun _ => 1, ?_⟩
  have h1 : (Finset.image (fun _ : Fin 2 => true) Finset.univ) = {true} := by decide
  rw [h1]
  norm_num

end TimeWarp
