/-
**Proposition `prop:versionCount`** (version-count generalization bound), Eqs.
`eq:versionCountBound` and `eq:excessRisk`, and its proof.

The two concentration steps live in `TimeWarp/Sampling.lean`. This file carries them over to
the joint sample space, performs the "Union bound" and "Excess risk" steps, and states the
proposition.
-/
import TimeWarp.Sampling

set_option linter.unusedSectionVars false
set_option linter.style.haveILetI false

namespace TimeWarp

open MeasureTheory ProbabilityTheory Real
open scoped NNReal ENNReal

variable {V Z Θ : Type*}
variable [Fintype V] [MeasurableSpace V] [DiscreteMeasurableSpace V] [MeasurableSpace Z]
variable {ℓ : Θ → Z → ℝ} {B : ℝ} {D : V → Measure Z} [∀ v, IsProbabilityMeasure (D v)]
variable {P : Measure V} [IsProbabilityMeasure P] {k M : ℕ}

/-! ### Measurability of the events in the proof -/

instance : DiscreteMeasurableSpace (Vers V k) := inferInstance

theorem measurable_riskBar (θ : Θ) :
    Measurable fun ω : Sample V Z k M => riskBar D ℓ k ω.1 θ :=
  (Measurable.of_discrete (f := fun vs : Vers V k => riskBar D ℓ k vs θ)).comp measurable_fst

theorem measurable_riskHat (hℓ : LossBound ℓ B) (θ : Θ) :
    Measurable fun ω : Sample V Z k M => riskHat ℓ k M ω θ := by
  refine measurable_from_prod_countable_right fun vs => ?_
  simp only [riskHat, pairOf]
  exact (Finset.measurable_sum _ fun p _ =>
    (hℓ.meas θ).comp ((measurable_pi_apply (vs p.1)).comp (measurable_pi_apply p))).div_const _

/-! ### The four events of the proof, on the joint sample space -/

/-- `L_𝒫(θ) - \bar L_tr(θ) ≥ ε`: the across-version deviation that Eq. `eq:versionCountBound`
must control, for every `θ`. -/
def acrossUp (P : Measure V) (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (k M : ℕ) (θ : Θ) (ε : ℝ) :
    Set (Sample V Z k M) :=
  {ω | ε ≤ riskP P D ℓ θ - riskBar D ℓ k ω.1 θ}

/-- `\bar L_tr(θ) - L_𝒫(θ) ≥ ε`: the reverse deviation, needed only at the fixed minimiser. -/
def acrossDown (P : Measure V) (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (k M : ℕ) (θ : Θ) (ε : ℝ) :
    Set (Sample V Z k M) :=
  {ω | ε ≤ riskBar D ℓ k ω.1 θ - riskP P D ℓ θ}

/-- `\bar L_tr(θ) - \hat L_tr(θ) ≥ ε`: the within-version deviation, for every `θ`. -/
def withinUp (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (k M : ℕ) (θ : Θ) (ε : ℝ) :
    Set (Sample V Z k M) :=
  {ω | ε ≤ riskBar D ℓ k ω.1 θ - riskHat ℓ k M ω θ}

/-- `\hat L_tr(θ) - \bar L_tr(θ) ≥ ε`: the reverse deviation, needed only at the minimiser. -/
def withinDown (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (k M : ℕ) (θ : Θ) (ε : ℝ) :
    Set (Sample V Z k M) :=
  {ω | ε ≤ riskHat ℓ k M ω θ - riskBar D ℓ k ω.1 θ}

theorem measurableSet_acrossUp (θ : Θ) (ε : ℝ) :
    MeasurableSet (acrossUp P D ℓ k M θ ε) :=
  measurableSet_le measurable_const (measurable_const.sub (measurable_riskBar θ))

theorem measurableSet_acrossDown (θ : Θ) (ε : ℝ) :
    MeasurableSet (acrossDown P D ℓ k M θ ε) :=
  measurableSet_le measurable_const ((measurable_riskBar θ).sub measurable_const)

theorem measurableSet_withinUp (hℓ : LossBound ℓ B) (θ : Θ) (ε : ℝ) :
    MeasurableSet (withinUp D ℓ k M θ ε) :=
  measurableSet_le measurable_const ((measurable_riskBar θ).sub (measurable_riskHat hℓ θ))

theorem measurableSet_withinDown (hℓ : LossBound ℓ B) (θ : Θ) (ε : ℝ) :
    MeasurableSet (withinDown D ℓ k M θ ε) :=
  measurableSet_le measurable_const ((measurable_riskHat hℓ θ).sub (measurable_riskBar θ))

/-! ### Carrying the two concentration steps to the joint space -/

/-- An event that depends only on the drawn versions has the same probability on the joint
space as on the version space. -/
theorem sampleMeasure_real_fst (S : Set (Vers V k)) :
    (sampleMeasure P D k M).real {ω : Sample V Z k M | ω.1 ∈ S} = (versMeasure P k).real S := by
  have hset : {ω : Sample V Z k M | ω.1 ∈ S} = S ×ˢ (Set.univ : Set (Seeds V Z k M)) := by
    ext ω; simp
  rw [Measure.real, sampleMeasure, hset, Measure.prod_prod, measure_univ, mul_one]
  rfl

/-- "The right-hand side does not depend on `𝒱_tr`, so the same bound holds unconditionally":
a uniform bound on every conditional slice bounds the joint probability. -/
theorem sampleMeasure_real_le_of_slice {S : Set (Sample V Z k M)} (hS : MeasurableSet S)
    {c : ℝ} (hc : 0 ≤ c) (h : ∀ vs, (seedMeasure D k M).real (Prod.mk vs ⁻¹' S) ≤ c) :
    (sampleMeasure P D k M).real S ≤ c := by
  have hmeas : ∀ vs, (seedMeasure D k M) (Prod.mk vs ⁻¹' S) ≤ ENNReal.ofReal c := fun vs =>
    (ENNReal.le_ofReal_iff_toReal_le (measure_ne_top _ _) hc).2 (h vs)
  have hjoint : (sampleMeasure P D k M) S ≤ ENNReal.ofReal c := by
    rw [sampleMeasure, Measure.prod_apply hS]
    calc ∫⁻ vs, (seedMeasure D k M) (Prod.mk vs ⁻¹' S) ∂(versMeasure P k)
        ≤ ∫⁻ _, ENNReal.ofReal c ∂(versMeasure P k) := lintegral_mono hmeas
      _ = ENNReal.ofReal c := by simp
  exact ENNReal.toReal_le_of_le_ofReal hc hjoint

theorem real_acrossUp_le (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k) :
    (sampleMeasure P D k M).real (acrossUp P D ℓ k M θ ε) ≤ exp (-2 * k * ε ^ 2 / B ^ 2) := by
  rw [acrossUp, show {ω : Sample V Z k M | ε ≤ riskP P D ℓ θ - riskBar D ℓ k ω.1 θ}
        = {ω : Sample V Z k M | ω.1 ∈ {vs | ε ≤ riskP P D ℓ θ - riskBar D ℓ k vs θ}} from rfl,
    sampleMeasure_real_fst]
  exact across_versions hℓ θ hε hk

theorem real_acrossDown_le (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k) :
    (sampleMeasure P D k M).real (acrossDown P D ℓ k M θ ε) ≤ exp (-2 * k * ε ^ 2 / B ^ 2) := by
  rw [acrossDown, show {ω : Sample V Z k M | ε ≤ riskBar D ℓ k ω.1 θ - riskP P D ℓ θ}
        = {ω : Sample V Z k M | ω.1 ∈ {vs | ε ≤ riskBar D ℓ k vs θ - riskP P D ℓ θ}} from rfl,
    sampleMeasure_real_fst]
  exact across_versions_rev hℓ θ hε hk

theorem real_withinUp_le (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k)
    (hM : 0 < M) :
    (sampleMeasure P D k M).real (withinUp D ℓ k M θ ε)
      ≤ exp (-2 * (k * M) * ε ^ 2 / B ^ 2) :=
  sampleMeasure_real_le_of_slice (measurableSet_withinUp hℓ θ ε) (exp_nonneg _)
    fun vs => within_versions hℓ θ vs hε hk hM

theorem real_withinDown_le (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k)
    (hM : 0 < M) :
    (sampleMeasure P D k M).real (withinDown D ℓ k M θ ε)
      ≤ exp (-2 * (k * M) * ε ^ 2 / B ^ 2) :=
  sampleMeasure_real_le_of_slice (measurableSet_withinDown hℓ θ ε) (exp_nonneg _)
    fun vs => within_versions_rev hℓ θ vs hε hk hM

/-! ### The two radii `ε₁` and `ε₂` -/

/-- `ε₁ = B √(log(4|Θ|/δ) / (2k))`, the "across versions" term of Eq. `eq:versionCountBound`. -/
noncomputable def eps1 (B δ : ℝ) (n k : ℕ) : ℝ := B * √(log (4 * n / δ) / (2 * k))

/-- `ε₂ = B √(log(4|Θ|/δ) / (2kM))`, the "within versions" term of Eq. `eq:versionCountBound`. -/
noncomputable def eps2 (B δ : ℝ) (n k M : ℕ) : ℝ := B * √(log (4 * n / δ) / (2 * (k * M)))

theorem eps1_nonneg (hB : 0 ≤ B) {δ : ℝ} {n k : ℕ} : 0 ≤ eps1 B δ n k :=
  mul_nonneg hB (Real.sqrt_nonneg _)

theorem eps2_nonneg (hB : 0 ≤ B) {δ : ℝ} {n k M : ℕ} : 0 ≤ eps2 B δ n k M :=
  mul_nonneg hB (Real.sqrt_nonneg _)

section Calibration

variable {δ : ℝ} {n : ℕ}

private theorem eta_pos (hδ0 : 0 < δ) (hn : 0 < n) : 0 < δ / (4 * n) := by
  have : (0:ℝ) < 4 * n := by positivity
  positivity

private theorem eta_le_one (hδ0 : 0 < δ) (hδ1 : δ < 1) (hn : 0 < n) : δ / (4 * n) ≤ 1 := by
  have hn1 : (1:ℝ) ≤ n := by exact_mod_cast hn
  rw [div_le_one (by positivity)]
  linarith

private theorem one_div_eta (δ : ℝ) (n : ℕ) : 1 / (δ / (4 * n)) = 4 * n / δ := by
  rw [one_div_div]

/-- Calibration of `ε₁`: `exp(-2k ε₁²/B²) = δ/(4|Θ|)`. -/
theorem exp_eps1 (hB : 0 < B) (hk : 0 < k) (hn : 0 < n) (hδ0 : 0 < δ) (hδ1 : δ < 1) :
    exp (-2 * k * (eps1 B δ n k) ^ 2 / B ^ 2) = δ / (4 * n) := by
  have h := exp_hoeffding_calibrated (B := B) (η := δ / (4 * n)) (n := k) hB hk
    (eta_pos hδ0 hn) (eta_le_one hδ0 hδ1 hn)
  rwa [one_div_eta δ n] at h

/-- Calibration of `ε₂`: `exp(-2kM ε₂²/B²) = δ/(4|Θ|)`. -/
theorem exp_eps2 (hB : 0 < B) (hk : 0 < k) (hM : 0 < M) (hn : 0 < n) (hδ0 : 0 < δ)
    (hδ1 : δ < 1) :
    exp (-2 * (k * M) * (eps2 B δ n k M) ^ 2 / B ^ 2) = δ / (4 * n) := by
  have hkM : 0 < k * M := Nat.mul_pos hk hM
  have h := exp_hoeffding_calibrated (B := B) (η := δ / (4 * n)) (n := k * M) hB hkM
    (eta_pos hδ0 hn) (eta_le_one hδ0 hδ1 hn)
  rw [one_div_eta δ n] at h
  rw [eps2, ← h]
  push_cast
  ring_nf

end Calibration

/-! ### Union bound and the good event -/

section Main

variable [Fintype Θ] [Nonempty Θ]

/-- `Θ` finite and nonempty gives the fixed minimiser `θ^⋆ ∈ argmin_Θ L_𝒫` that the union-bound
step of the proof singles out. -/
theorem exists_min_riskP (P : Measure V) (D : V → Measure Z) (ℓ : Θ → Z → ℝ) :
    ∃ θstar : Θ, ∀ θ, riskP P D ℓ θstar ≤ riskP P D ℓ θ :=
  Finite.exists_min _

/-- The complement of the good event of the proof: the `2|Θ|` upper-deviation events (both
terms, all `θ`) together with the two lower-deviation events at the fixed minimiser `θ*`. -/
def badEvent (P : Measure V) (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (B : ℝ) (k M n : ℕ)
    (θstar : Θ) (δ : ℝ) : Set (Sample V Z k M) :=
  (⋃ θ : Θ, acrossUp P D ℓ k M θ (eps1 B δ n k)) ∪
  (⋃ θ : Θ, withinUp D ℓ k M θ (eps2 B δ n k M)) ∪
  acrossDown P D ℓ k M θstar (eps1 B δ n k) ∪
  withinDown D ℓ k M θstar (eps2 B δ n k M)

theorem measurableSet_badEvent (hℓ : LossBound ℓ B) (n : ℕ) (θstar : Θ) (δ : ℝ) :
    MeasurableSet (badEvent P D ℓ B k M n θstar δ) :=
  (((MeasurableSet.iUnion fun θ => measurableSet_acrossUp θ _).union
    (MeasurableSet.iUnion fun θ => measurableSet_withinUp hℓ θ _)).union
    (measurableSet_acrossDown θstar _)).union (measurableSet_withinDown hℓ θstar _)

/-- **"Union bound"** step of the proof of Proposition `prop:versionCount`.

The `2|Θ|` upper-deviation events have probability at most `δ/(4|Θ|)` each and contribute
`δ/2`; the two lower-deviation events at `θ*` contribute `δ/(2|Θ|) ≤ δ/2`. -/
theorem real_badEvent_le (hℓ : LossBound ℓ B) (θstar : Θ) {δ : ℝ} (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hk : 0 < k) (hM : 0 < M) :
    (sampleMeasure P D k M).real (badEvent P D ℓ B k M (Fintype.card Θ) θstar δ) ≤ δ := by
  classical
  set n := Fintype.card Θ with hn
  have hn0 : 0 < n := Fintype.card_pos
  have hn1 : (1:ℝ) ≤ (n:ℝ) := by exact_mod_cast hn0
  have hcal1 := exp_eps1 (B := B) (k := k) (n := n) hℓ.pos hk hn0 hδ0 hδ1
  have hcal2 := exp_eps2 (B := B) (k := k) (M := M) (n := n) hℓ.pos hk hM hn0 hδ0 hδ1
  have hA : ∀ θ : Θ, (sampleMeasure P D k M).real (acrossUp P D ℓ k M θ (eps1 B δ n k))
      ≤ δ / (4 * (n:ℝ)) := fun θ => by
    rw [← hcal1]
    exact real_acrossUp_le (P := P) (M := M) hℓ θ (eps1_nonneg hℓ.pos.le) hk
  have hW : ∀ θ : Θ, (sampleMeasure P D k M).real (withinUp D ℓ k M θ (eps2 B δ n k M))
      ≤ δ / (4 * (n:ℝ)) := fun θ => by
    rw [← hcal2]
    exact real_withinUp_le (P := P) hℓ θ (eps2_nonneg hℓ.pos.le) hk hM
  have hAd : (sampleMeasure P D k M).real (acrossDown P D ℓ k M θstar (eps1 B δ n k))
      ≤ δ / (4 * (n:ℝ)) := by
    rw [← hcal1]
    exact real_acrossDown_le (P := P) (M := M) hℓ θstar (eps1_nonneg hℓ.pos.le) hk
  have hWd : (sampleMeasure P D k M).real (withinDown D ℓ k M θstar (eps2 B δ n k M))
      ≤ δ / (4 * (n:ℝ)) := by
    rw [← hcal2]
    exact real_withinDown_le (P := P) hℓ θstar (eps2_nonneg hℓ.pos.le) hk hM
  have hsum : ∑ _θ : Θ, δ / (4 * (n:ℝ)) = δ / 4 := by
    rw [Finset.sum_const, Finset.card_univ, ← hn, nsmul_eq_mul]
    field_simp
  have hUA : (sampleMeasure P D k M).real (⋃ θ : Θ, acrossUp P D ℓ k M θ (eps1 B δ n k))
      ≤ δ / 4 :=
    (measureReal_iUnion_fintype_le _).trans
      ((Finset.sum_le_sum fun θ _ => hA θ).trans hsum.le)
  have hUW : (sampleMeasure P D k M).real (⋃ θ : Θ, withinUp D ℓ k M θ (eps2 B δ n k M))
      ≤ δ / 4 :=
    (measureReal_iUnion_fintype_le _).trans
      ((Finset.sum_le_sum fun θ _ => hW θ).trans hsum.le)
  have hstep : (sampleMeasure P D k M).real (badEvent P D ℓ B k M n θstar δ)
      ≤ δ / 4 + δ / 4 + δ / (4 * (n:ℝ)) + δ / (4 * (n:ℝ)) := by
    refine (measureReal_union_le _ _).trans (add_le_add ?_ hWd)
    refine (measureReal_union_le _ _).trans (add_le_add ?_ hAd)
    exact (measureReal_union_le _ _).trans (add_le_add hUA hUW)
  have hfrac : δ / (4 * (n:ℝ)) ≤ δ / 4 :=
    div_le_div_of_nonneg_left hδ0.le (by norm_num) (by nlinarith)
  linarith

/-- **Proposition `prop:versionCount`** (version-count generalization bound).

`G` is the event of the proof: "On the complement, which has probability at least `1-δ`,
Eq. `eq:versionCountBound` holds for every `θ`, and in addition
`\hat L_tr(θ*) ≤ L_𝒫(θ*) + ε₁ + ε₂`."

* the third conclusion is Eq. `eq:versionCountBound`;
* the fourth is Eq. `eq:excessRisk`, whose right-hand side is `min_θ L_𝒫(θ)` because
  `θstar` attains that minimum (`exists_min_riskP`).

Note that the fourth conclusion is *not* a consequence of the third alone: it needs the two
lower-deviation events at `θ*`, which the proof does include in its union bound. -/
theorem versionCount (hℓ : LossBound ℓ B) (hk : 0 < k) (hM : 0 < M)
    {δ : ℝ} (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (θstar : Θ) (hθstar : ∀ θ, riskP P D ℓ θstar ≤ riskP P D ℓ θ) :
    ∃ G : Set (Sample V Z k M),
      MeasurableSet G ∧
      1 - δ ≤ (sampleMeasure P D k M).real G ∧
      (∀ ω ∈ G, ∀ θ : Θ,
        riskP P D ℓ θ ≤ riskHat ℓ k M ω θ
          + eps2 B δ (Fintype.card Θ) k M + eps1 B δ (Fintype.card Θ) k) ∧
      (∀ ω ∈ G, ∀ θhat : Θ, (∀ θ, riskHat ℓ k M ω θhat ≤ riskHat ℓ k M ω θ) →
        ∀ θ : Θ, riskP P D ℓ θhat ≤ riskP P D ℓ θ
          + 2 * eps2 B δ (Fintype.card Θ) k M + 2 * eps1 B δ (Fintype.card Θ) k) := by
  classical
  set n := Fintype.card Θ with hn
  refine ⟨(badEvent P D ℓ B k M n θstar δ)ᶜ,
    (measurableSet_badEvent (P := P) (D := D) (k := k) (M := M) hℓ n θstar δ).compl,
      ?_, ?_, ?_⟩
  · have h1 := real_badEvent_le (P := P) (D := D) (k := k) (M := M) hℓ θstar hδ0 hδ1 hk hM
    have h2 := measureReal_add_measureReal_compl (μ := sampleMeasure P D k M)
      (measurableSet_badEvent (P := P) (D := D) (k := k) (M := M) hℓ n θstar δ)
    have huniv : (sampleMeasure P D k M).real Set.univ = 1 := by
      simp [Measure.real, measure_univ]
    rw [huniv] at h2
    rw [← hn] at h1
    linarith
  · intro ω hω θ
    simp only [badEvent, Set.mem_compl_iff, Set.mem_union, Set.mem_iUnion, not_or, not_exists,
      acrossUp, withinUp, acrossDown, withinDown, Set.mem_setOf_eq, not_le] at hω
    obtain ⟨⟨⟨h1, h2⟩, _h3⟩, _h4⟩ := hω
    have := h1 θ
    have := h2 θ
    linarith
  · intro ω hω θhat hmin θ
    simp only [badEvent, Set.mem_compl_iff, Set.mem_union, Set.mem_iUnion, not_or, not_exists,
      acrossUp, withinUp, acrossDown, withinDown, Set.mem_setOf_eq, not_le] at hω
    obtain ⟨⟨⟨h1, h2⟩, h3⟩, h4⟩ := hω
    have ha := h1 θhat
    have hb := h2 θhat
    have hc := hmin θstar
    have hd := hθstar θ
    linarith

end Main

end TimeWarp
