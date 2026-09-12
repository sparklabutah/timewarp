/-
The sampling model of Proposition `prop:versionCount` and the two concentration steps of its
proof ("Across versions" and "Within versions").

**Setting.** `V` indexes the versions, `Z` is the space of history-response pairs `(h,y)`,
`Θ` the policy class. `P` is the distribution `𝒫` over versions, `D v` the teacher
distribution `𝒟_{τ,v}` on version `v`, and `ℓ θ z` the per-sample loss `ℓ(θ;h,y)`.

**The probability space.** The proposition draws `k` versions i.i.d. from `𝒫` and then, given
the versions, `M` pairs per version i.i.d. from `𝒟_{τ,v}`. That two-stage experiment is
realised here on a single product space: alongside the `k` versions we draw, for each of the
`k·M` sample slots, one pair *per version* from `⨂_v 𝒟_{τ,v}`, and read off the coordinate of
the version that was actually drawn. The read-off coordinate has law `𝒟_{τ,v}` and the slots
are independent, so this is the experiment of the proposition, written as a plain product
measure (no kernels needed).
-/
import TimeWarp.Hoeffding
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Measure.Prod

set_option linter.unusedSectionVars false
set_option linter.style.haveILetI false

namespace TimeWarp

open MeasureTheory ProbabilityTheory Real
open scoped NNReal ENNReal

/-! ### Integrals against a coordinate of a product measure -/

/-- The `i`-th coordinate of a product of probability measures has law `m i`. -/
theorem integral_eval_pi {ι : Type*} [Fintype ι] {α : ι → Type*}
    [∀ i, MeasurableSpace (α i)] (m : ∀ i, Measure (α i)) [∀ i, IsProbabilityMeasure (m i)]
    (i : ι) {g : α i → ℝ} (hg : Measurable g) :
    ∫ x, g (x i) ∂(Measure.pi m) = ∫ y, g y ∂(m i) := by
  have hmp := MeasureTheory.measurePreserving_eval m i
  rw [← hmp.map_eq, integral_map (measurable_pi_apply i).aemeasurable hg.aestronglyMeasurable]

/-! ### The model -/

variable {V Z Θ : Type*}

/-- The `k` versions drawn from `𝒫`. -/
abbrev Vers (V : Type*) (k : ℕ) := Fin k → V

/-- One coupled draw per version for each of the `k·M` sample slots. -/
abbrev Seeds (V Z : Type*) (k M : ℕ) := Fin k × Fin M → (V → Z)

/-- One run of the experiment: the drawn versions together with the drawn pairs. -/
abbrev Sample (V Z : Type*) (k M : ℕ) := Vers V k × Seeds V Z k M

section Defs

variable [Fintype V] [MeasurableSpace V] [MeasurableSpace Z]

/-- `𝒫^k`, the law of the `k` training versions. -/
noncomputable def versMeasure (P : Measure V) (k : ℕ) : Measure (Vers V k) :=
  Measure.pi fun _ => P

/-- The law of the `k·M` coupled pair draws. -/
noncomputable def seedMeasure (D : V → Measure Z) (k M : ℕ) : Measure (Seeds V Z k M) :=
  Measure.pi fun _ => Measure.pi D

/-- The law of one run of the experiment. -/
noncomputable def sampleMeasure (P : Measure V) (D : V → Measure Z) (k M : ℕ) :
    Measure (Sample V Z k M) := (versMeasure P k).prod (seedMeasure D k M)

instance (P : Measure V) [IsProbabilityMeasure P] (k : ℕ) :
    IsProbabilityMeasure (versMeasure P k) := by
  unfold versMeasure; infer_instance

instance (D : V → Measure Z) [∀ v, IsProbabilityMeasure (D v)] (k M : ℕ) :
    IsProbabilityMeasure (seedMeasure D k M) := by
  unfold seedMeasure; infer_instance

instance (P : Measure V) [IsProbabilityMeasure P] (D : V → Measure Z)
    [∀ v, IsProbabilityMeasure (D v)] (k M : ℕ) :
    IsProbabilityMeasure (sampleMeasure P D k M) := by
  unfold sampleMeasure; infer_instance

/-- The `j`-th pair drawn on the `i`-th training version. -/
def pairOf (k M : ℕ) (ω : Sample V Z k M) (p : Fin k × Fin M) : Z := ω.2 p (ω.1 p.1)

/-- Eq. `eq:versionRisk`: the risk `L_v(θ)` of `θ` on version `v`. -/
noncomputable def riskV (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (v : V) (θ : Θ) : ℝ :=
  ∫ z, ℓ θ z ∂(D v)

/-- Eq. `eq:freshRisk`: the expected risk `L_𝒫(θ)` on a fresh version. -/
noncomputable def riskP (P : Measure V) (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (θ : Θ) : ℝ :=
  ∫ v, riskV D ℓ v θ ∂P

/-- `\bar L_tr(θ)`: the average population risk over the drawn versions. -/
noncomputable def riskBar (D : V → Measure Z) (ℓ : Θ → Z → ℝ) (k : ℕ)
    (vs : Vers V k) (θ : Θ) : ℝ := (∑ i, riskV D ℓ (vs i) θ) / k

/-- Eq. `eq:pooledRisk`: the pooled empirical risk `\hat L_tr(θ)` that \timewarp-BC minimises. -/
noncomputable def riskHat (ℓ : Θ → Z → ℝ) (k M : ℕ) (ω : Sample V Z k M) (θ : Θ) : ℝ :=
  (∑ p : Fin k × Fin M, ℓ θ (pairOf k M ω p)) / (k * M)

/-- Assumption `ass:bounded`, first half: `0 ≤ ℓ(θ;h,y) ≤ B` with `B > 0`, together with the
measurability of `ℓ` that is needed for the risks of Eq. `eq:versionRisk` to be defined. -/
structure LossBound (ℓ : Θ → Z → ℝ) (B : ℝ) : Prop where
  pos : 0 < B
  meas : ∀ θ, Measurable (ℓ θ)
  mem : ∀ θ z, ℓ θ z ∈ Set.Icc (0:ℝ) B

end Defs

/-! ### The risks inherit the bound `[0,B]` -/

section Bounds

variable [Fintype V] [MeasurableSpace V] [MeasurableSpace Z] {ℓ : Θ → Z → ℝ} {B : ℝ}
variable {D : V → Measure Z} [∀ v, IsProbabilityMeasure (D v)]

theorem LossBound.integrable (hℓ : LossBound ℓ B) (θ : Θ) (v : V) :
    Integrable (ℓ θ) (D v) :=
  Integrable.of_mem_Icc (μ := D v) 0 B (hℓ.meas θ).aemeasurable
    (Filter.Eventually.of_forall (hℓ.mem θ))

theorem LossBound.riskV_mem (hℓ : LossBound ℓ B) (v : V) (θ : Θ) :
    riskV D ℓ v θ ∈ Set.Icc (0:ℝ) B := by
  refine ⟨integral_nonneg fun z => (hℓ.mem θ z).1, ?_⟩
  calc riskV D ℓ v θ ≤ ∫ _z : Z, B ∂(D v) :=
        integral_mono (hℓ.integrable θ v) (integrable_const (μ := D v) B)
          fun z => (hℓ.mem θ z).2
    _ = B := by simp

theorem LossBound.riskV_meas (_hℓ : LossBound ℓ B) (θ : Θ)
    [DiscreteMeasurableSpace V] : Measurable fun v => riskV D ℓ v θ :=
  Measurable.of_discrete

theorem LossBound.riskP_mem (hℓ : LossBound ℓ B) {P : Measure V} [IsProbabilityMeasure P]
    [DiscreteMeasurableSpace V] (θ : Θ) :
    riskP P D ℓ θ ∈ Set.Icc (0:ℝ) B := by
  have hint : Integrable (fun v => riskV D ℓ v θ) P :=
    Integrable.of_mem_Icc (μ := P) 0 B (hℓ.riskV_meas θ).aemeasurable
      (Filter.Eventually.of_forall fun v => hℓ.riskV_mem v θ)
  refine ⟨integral_nonneg fun v => (hℓ.riskV_mem v θ).1, ?_⟩
  calc riskP P D ℓ θ ≤ ∫ _v : V, B ∂P :=
        integral_mono hint (integrable_const (μ := P) B) fun v => (hℓ.riskV_mem v θ).2
    _ = B := by simp

end Bounds

/-! ### "Across versions": Hoeffding over the `k` drawn versions -/

section Across

variable [Fintype V] [MeasurableSpace V] [DiscreteMeasurableSpace V] [MeasurableSpace Z]
variable {ℓ : Θ → Z → ℝ} {B : ℝ} {D : V → Measure Z} [∀ v, IsProbabilityMeasure (D v)]
variable {P : Measure V} [IsProbabilityMeasure P] {k M : ℕ}

/-- The `k` values `L_v(θ)`, `v ∈ 𝒱_tr`, are i.i.d. -/
theorem indep_riskV (θ : Θ) :
    iIndepFun (fun (i : Fin k) (vs : Vers V k) => riskV D ℓ (vs i) θ) (versMeasure P k) :=
  iIndepFun_pi (X := fun _ : Fin k => fun v : V => riskV D ℓ v θ)
    fun _ => (Measurable.of_discrete).aemeasurable

/-- ... and they have mean `L_𝒫(θ)` by Eq. `eq:freshRisk`. -/
theorem integral_riskV (hℓ : LossBound ℓ B) (θ : Θ) (i : Fin k) :
    ∫ vs, riskV D ℓ (vs i) θ ∂(versMeasure P k) = riskP P D ℓ θ :=
  integral_eval_pi (fun _ => P) i (hℓ.riskV_meas θ)

/-- **"Across versions"** of the proof of Proposition `prop:versionCount`:
`Pr[ L_𝒫(θ) - \bar L_tr(θ) ≥ ε ] ≤ exp(-2kε²/B²)`. -/
theorem across_versions (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k) :
    (versMeasure P k).real {vs | ε ≤ riskP P D ℓ θ - riskBar D ℓ k vs θ}
      ≤ exp (-2 * k * ε ^ 2 / B ^ 2) := by
  haveI : Nonempty (Fin k) := Fin.pos_iff_nonempty.1 hk
  have hcard : (Fintype.card (Fin k) : ℝ) = k := by simp
  have hk0 : (0:ℝ) < k := by exact_mod_cast hk
  have key := hoeffding_mean_le (μ := versMeasure P k)
    (X := fun (i : Fin k) (vs : Vers V k) => riskV D ℓ (vs i) θ) hℓ.pos
    (fun _ => (Measurable.of_discrete).aemeasurable) (indep_riskV θ)
    (fun _ => Filter.Eventually.of_forall fun vs => hℓ.riskV_mem _ θ) hε
  rw [hcard] at key
  refine le_trans (le_of_eq ?_) key
  congr 1
  ext vs
  have h1 : (∑ _i : Fin k, riskP P D ℓ θ) / (k:ℝ) = riskP P D ℓ θ := by
    rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    field_simp
  simp only [Set.mem_setOf_eq, integral_riskV hℓ θ, h1, riskBar]

/-- The other direction of "Across versions", needed for the fixed minimiser `θ*`:
`Pr[ \bar L_tr(θ) - L_𝒫(θ) ≥ ε ] ≤ exp(-2kε²/B²)`. -/
theorem across_versions_rev (hℓ : LossBound ℓ B) (θ : Θ) {ε : ℝ} (hε : 0 ≤ ε) (hk : 0 < k) :
    (versMeasure P k).real {vs | ε ≤ riskBar D ℓ k vs θ - riskP P D ℓ θ}
      ≤ exp (-2 * k * ε ^ 2 / B ^ 2) := by
  haveI : Nonempty (Fin k) := Fin.pos_iff_nonempty.1 hk
  have hcard : (Fintype.card (Fin k) : ℝ) = k := by simp
  have hk0 : (0:ℝ) < k := by exact_mod_cast hk
  have key := hoeffding_mean_ge (μ := versMeasure P k)
    (X := fun (i : Fin k) (vs : Vers V k) => riskV D ℓ (vs i) θ) hℓ.pos
    (fun _ => (Measurable.of_discrete).aemeasurable) (indep_riskV θ)
    (fun _ => Filter.Eventually.of_forall fun vs => hℓ.riskV_mem _ θ) hε
  rw [hcard] at key
  refine le_trans (le_of_eq ?_) key
  congr 1
  ext vs
  have h1 : (∑ _i : Fin k, riskP P D ℓ θ) / (k:ℝ) = riskP P D ℓ θ := by
    rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    field_simp
  simp only [Set.mem_setOf_eq, integral_riskV hℓ θ, h1, riskBar]

end Across

/-! ### "Within versions": Hoeffding over the `k·M` pairs, conditionally on the versions -/

section Within

variable [Fintype V] [MeasurableSpace V] [DiscreteMeasurableSpace V] [MeasurableSpace Z]
variable {ℓ : Θ → Z → ℝ} {B : ℝ} {D : V → Measure Z} [∀ v, IsProbabilityMeasure (D v)]
variable {k M : ℕ}

/-- Conditionally on the drawn versions, the `k·M` losses are independent. -/
theorem indep_loss (hℓ : LossBound ℓ B) (θ : Θ) (vs : Vers V k) :
    iIndepFun (fun (p : Fin k × Fin M) (ξ : Seeds V Z k M) => ℓ θ (ξ p (vs p.1)))
      (seedMeasure D k M) :=
  iIndepFun_pi (X := fun p : Fin k × Fin M => fun ζ : V → Z => ℓ θ (ζ (vs p.1)))
    fun p => ((hℓ.meas θ).comp (measurable_pi_apply (vs p.1))).aemeasurable

/-- ... and the `(i,j)`-th one has mean `L_{v_i}(θ)`, by Eq. `eq:versionRisk`. -/
theorem integral_loss (hℓ : LossBound ℓ B) (θ : Θ) (vs : Vers V k) (p : Fin k × Fin M) :
    ∫ ξ, ℓ θ (ξ p (vs p.1)) ∂(seedMeasure D k M) = riskV D ℓ (vs p.1) θ := by
  have h1 : (∫ ξ : Seeds V Z k M, ℓ θ (ξ p (vs p.1)) ∂(seedMeasure D k M))
      = ∫ ζ : V → Z, ℓ θ (ζ (vs p.1)) ∂(Measure.pi D) :=
    integral_eval_pi (α := fun _ : Fin k × Fin M => (V → Z)) (fun _ => Measure.pi D) p
      (g := fun ζ : V → Z => ℓ θ (ζ (vs p.1)))
      ((hℓ.meas θ).comp (measurable_pi_apply (vs p.1)))
  have h2 : (∫ ζ : V → Z, ℓ θ (ζ (vs p.1)) ∂(Measure.pi D)) = ∫ z, ℓ θ z ∂(D (vs p.1)) :=
    integral_eval_pi D (vs p.1) (g := ℓ θ) (hℓ.meas θ)
  rw [h1, h2]
  rfl

/-- The mean of the `k·M` conditional means is `\bar L_tr(θ)`. -/
theorem sum_integral_loss (hℓ : LossBound ℓ B) (θ : Θ) (vs : Vers V k) (hk : 0 < k)
    (hM : 0 < M) :
    (∑ p : Fin k × Fin M, ∫ ξ, ℓ θ (ξ p (vs p.1)) ∂(seedMeasure D k M))
        / (Fintype.card (Fin k × Fin M))
      = riskBar D ℓ k vs θ := by
  have hk0 : (0:ℝ) < k := by exact_mod_cast hk
  have hM0 : (0:ℝ) < M := by exact_mod_cast hM
  simp only [integral_loss hℓ θ vs]
  rw [Fintype.sum_prod_type]
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  rw [← Finset.mul_sum]
  simp only [Fintype.card_prod, Fintype.card_fin, riskBar]
  push_cast
  rw [mul_comm (k:ℝ) (M:ℝ), mul_div_mul_left _ _ (ne_of_gt hM0)]

/-- **"Within versions"** of the proof of Proposition `prop:versionCount`, conditionally on the
drawn versions: `Pr[ \bar L_tr(θ) - \hat L_tr(θ) ≥ ε | 𝒱_tr ] ≤ exp(-2kMε²/B²)`.

The right-hand side does not depend on `𝒱_tr`, which is what lets the proof drop the
conditioning; see `within_versions_uncond`. -/
theorem within_versions (hℓ : LossBound ℓ B) (θ : Θ) (vs : Vers V k) {ε : ℝ} (hε : 0 ≤ ε)
    (hk : 0 < k) (hM : 0 < M) :
    (seedMeasure D k M).real
        {ξ | ε ≤ riskBar D ℓ k vs θ - riskHat ℓ k M (vs, ξ) θ}
      ≤ exp (-2 * (k * M) * ε ^ 2 / B ^ 2) := by
  haveI : Nonempty (Fin k) := Fin.pos_iff_nonempty.1 hk
  haveI : Nonempty (Fin M) := Fin.pos_iff_nonempty.1 hM
  haveI : Nonempty (Fin k × Fin M) := inferInstance
  have hcard : (Fintype.card (Fin k × Fin M) : ℝ) = (k : ℝ) * M := by simp
  have key := hoeffding_mean_le (μ := seedMeasure D k M)
    (X := fun (p : Fin k × Fin M) (ξ : Seeds V Z k M) => ℓ θ (ξ p (vs p.1))) hℓ.pos
    (fun p => ((hℓ.meas θ).comp
      ((measurable_pi_apply (vs p.1)).comp (measurable_pi_apply p))).aemeasurable)
    (indep_loss hℓ θ vs)
    (fun p => Filter.Eventually.of_forall fun ξ => hℓ.mem θ _) hε
  rw [hcard] at key
  refine le_trans (le_of_eq ?_) key
  congr 1
  ext ξ
  have h2 := sum_integral_loss (D := D) hℓ θ vs hk hM
  rw [hcard] at h2
  simp only [Set.mem_setOf_eq, h2, riskHat, pairOf]

/-- The other direction of "Within versions", needed for the fixed minimiser `θ*`:
`Pr[ \hat L_tr(θ) - \bar L_tr(θ) ≥ ε | 𝒱_tr ] ≤ exp(-2kMε²/B²)`. -/
theorem within_versions_rev (hℓ : LossBound ℓ B) (θ : Θ) (vs : Vers V k) {ε : ℝ} (hε : 0 ≤ ε)
    (hk : 0 < k) (hM : 0 < M) :
    (seedMeasure D k M).real
        {ξ | ε ≤ riskHat ℓ k M (vs, ξ) θ - riskBar D ℓ k vs θ}
      ≤ exp (-2 * (k * M) * ε ^ 2 / B ^ 2) := by
  haveI : Nonempty (Fin k) := Fin.pos_iff_nonempty.1 hk
  haveI : Nonempty (Fin M) := Fin.pos_iff_nonempty.1 hM
  haveI : Nonempty (Fin k × Fin M) := inferInstance
  have hcard : (Fintype.card (Fin k × Fin M) : ℝ) = (k : ℝ) * M := by simp
  have key := hoeffding_mean_ge (μ := seedMeasure D k M)
    (X := fun (p : Fin k × Fin M) (ξ : Seeds V Z k M) => ℓ θ (ξ p (vs p.1))) hℓ.pos
    (fun p => ((hℓ.meas θ).comp
      ((measurable_pi_apply (vs p.1)).comp (measurable_pi_apply p))).aemeasurable)
    (indep_loss hℓ θ vs)
    (fun p => Filter.Eventually.of_forall fun ξ => hℓ.mem θ _) hε
  rw [hcard] at key
  refine le_trans (le_of_eq ?_) key
  congr 1
  ext ξ
  have h2 := sum_integral_loss (D := D) hℓ θ vs hk hM
  rw [hcard] at h2
  simp only [Set.mem_setOf_eq, h2, riskHat, pairOf]

end Within

end TimeWarp
