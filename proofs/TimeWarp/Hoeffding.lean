/-
Hoeffding's inequality in exactly the shape used by the proof of Proposition
`prop:versionCount`: for `n` independent random variables with values in `[0,B]`,
the sample mean deviates from the mean of the means by at least `ε` with probability at most
`exp(-2 n ε² / B²)`.

The paper cites this as "Hoeffding's inequality". It is *derived* here from Mathlib's
`ProbabilityTheory.hasSubgaussianMGF_of_mem_Icc` (Hoeffding's lemma) and
`ProbabilityTheory.HasSubgaussianMGF.measure_sum_ge_le_of_iIndepFun` (the sub-Gaussian tail
bound), so nothing in this development is assumed.

The file also records the calibration `ε = B √(log(1/η)/(2n)) ⟹ exp(-2nε²/B²) = η`
used in the "Union bound" step of the proof.
-/
import Mathlib.Probability.Moments.SubGaussian

set_option linter.unusedSectionVars false

namespace TimeWarp

open MeasureTheory ProbabilityTheory Real
open scoped NNReal ENNReal

variable {Ω ι : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
variable [Fintype ι] [Nonempty ι] {X : ι → Ω → ℝ} {B ε : ℝ}

/-- **Hoeffding's inequality**, upper deviation of the sample mean:
`Pr[ (1/n) Σᵢ Xᵢ - (1/n) Σᵢ E[Xᵢ] ≥ ε ] ≤ exp(-2nε²/B²)`. -/
theorem hoeffding_mean_ge (hB : 0 < B) (hmeas : ∀ i, AEMeasurable (X i) μ)
    (hindep : iIndepFun X μ) (hbdd : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) B) (hε : 0 ≤ ε) :
    μ.real {ω | ε ≤ (∑ i, X i ω) / (Fintype.card ι)
                      - (∑ i, ∫ x, X i x ∂μ) / (Fintype.card ι)}
      ≤ exp (-2 * (Fintype.card ι) * ε ^ 2 / B ^ 2) := by
  classical
  have hn0 : (0:ℝ) < (Fintype.card ι : ℝ) := by
    exact_mod_cast (Fintype.card_pos (α := ι))
  have hsubG : ∀ i ∈ (Finset.univ : Finset ι),
      HasSubgaussianMGF (fun ω => X i ω - ∫ x, X i x ∂μ) ((‖B - (0:ℝ)‖₊ / 2) ^ 2) μ :=
    fun i _ => hasSubgaussianMGF_of_mem_Icc (hmeas i) (hbdd i)
  have hindepY : iIndepFun (fun i ω => X i ω - ∫ x, X i x ∂μ) μ :=
    hindep.comp (fun i (x : ℝ) => x - ∫ x, X i x ∂μ) fun _ => measurable_sub_const _
  have key := HasSubgaussianMGF.measure_sum_ge_le_of_iIndepFun hindepY hsubG
    (ε := (Fintype.card ι : ℝ) * ε) (by positivity)
  have hset : {ω | (Fintype.card ι : ℝ) * ε ≤ ∑ i ∈ Finset.univ, (X i ω - ∫ x, X i x ∂μ)}
      = {ω | ε ≤ (∑ i, X i ω) / (Fintype.card ι)
                    - (∑ i, ∫ x, X i x ∂μ) / (Fintype.card ι)} := by
    ext ω
    simp only [Set.mem_setOf_eq, Finset.sum_sub_distrib]
    rw [← sub_div, le_div_iff₀ hn0, mul_comm]
  rw [hset] at key
  refine key.trans (le_of_eq ?_)
  have hcsum : ((∑ _i : ι, ((‖B - (0:ℝ)‖₊ / 2) ^ 2 : ℝ≥0) : ℝ≥0) : ℝ)
      = (Fintype.card ι : ℝ) * (B / 2) ^ 2 := by
    push_cast [Finset.sum_const, Finset.card_univ, nsmul_eq_mul, Real.norm_eq_abs, sub_zero,
      abs_of_nonneg hB.le]
    ring
  rw [hcsum]
  have hB2 : B ^ 2 ≠ 0 := by positivity
  have hnne : (Fintype.card ι : ℝ) ≠ 0 := ne_of_gt hn0
  congr 1
  field_simp
  try ring

/-- **Hoeffding's inequality**, lower deviation of the sample mean. This is the direction the
proof of Proposition `prop:versionCount` uses ("and the same bound holds for the deviation in
the other direction"):
`Pr[ (1/n) Σᵢ E[Xᵢ] - (1/n) Σᵢ Xᵢ ≥ ε ] ≤ exp(-2nε²/B²)`. -/
theorem hoeffding_mean_le (hB : 0 < B) (hmeas : ∀ i, AEMeasurable (X i) μ)
    (hindep : iIndepFun X μ) (hbdd : ∀ i, ∀ᵐ ω ∂μ, X i ω ∈ Set.Icc (0:ℝ) B) (hε : 0 ≤ ε) :
    μ.real {ω | ε ≤ (∑ i, ∫ x, X i x ∂μ) / (Fintype.card ι)
                      - (∑ i, X i ω) / (Fintype.card ι)}
      ≤ exp (-2 * (Fintype.card ι) * ε ^ 2 / B ^ 2) := by
  classical
  have hmeas' : ∀ i, AEMeasurable (fun ω => B - X i ω) μ := fun i => (hmeas i).const_sub _
  have hindep' : iIndepFun (fun i ω => B - X i ω) μ :=
    hindep.comp (fun _ (x : ℝ) => B - x) fun _ => measurable_const_sub _
  have hbdd' : ∀ i, ∀ᵐ ω ∂μ, (B - X i ω) ∈ Set.Icc (0:ℝ) B := by
    intro i
    filter_upwards [hbdd i] with ω hω
    obtain ⟨h0, hB'⟩ := hω
    exact ⟨by linarith, by linarith⟩
  have hint : ∀ i, Integrable (X i) μ := fun i => Integrable.of_mem_Icc 0 B (hmeas i) (hbdd i)
  have hmean : ∀ i, (∫ x, (B - X i x) ∂μ) = B - ∫ x, X i x ∂μ := fun i => by
    rw [integral_sub (integrable_const B) (hint i), integral_const]
    simp
  have key := hoeffding_mean_ge (X := fun i ω => B - X i ω) hB hmeas' hindep' hbdd' hε
  have hnne : (Fintype.card ι : ℝ) ≠ 0 := by
    have : (0:ℝ) < (Fintype.card ι : ℝ) := by exact_mod_cast (Fintype.card_pos (α := ι))
    exact ne_of_gt this
  refine le_trans (le_of_eq ?_) key
  congr 1
  ext ω
  have h1 : (∑ i, (B - X i ω)) = (Fintype.card ι : ℝ) * B - ∑ i, X i ω := by
    rw [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, nsmul_eq_mul]
  have h2 : (∑ i, ∫ x, (B - X i x) ∂μ)
      = (Fintype.card ι : ℝ) * B - ∑ i, ∫ x, X i x ∂μ := by
    simp only [hmean]
    rw [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, nsmul_eq_mul]
  have h3 : ((Fintype.card ι : ℝ) * B - ∑ i, X i ω) / (Fintype.card ι)
        - ((Fintype.card ι : ℝ) * B - ∑ i, ∫ x, X i x ∂μ) / (Fintype.card ι)
      = (∑ i, ∫ x, X i x ∂μ) / (Fintype.card ι) - (∑ i, X i ω) / (Fintype.card ι) := by
    field_simp
    ring
  simp only [Set.mem_setOf_eq, h1, h2, h3]

/-- The calibration used in the "Union bound" step of the proof of Proposition
`prop:versionCount`: choosing `ε = B √(log(1/η) / (2n))` makes Hoeffding's bound exactly `η`.

In the paper `η = δ/(4|Θ|)`; `ε₁` takes `n = k` and `ε₂` takes `n = kM`. -/
theorem exp_hoeffding_calibrated {B η : ℝ} {n : ℕ} (hB : 0 < B) (hn : 0 < n)
    (hη : 0 < η) (hη1 : η ≤ 1) :
    exp (-2 * n * (B * √(log (1 / η) / (2 * n))) ^ 2 / B ^ 2) = η := by
  have hn0 : (0:ℝ) < n := by exact_mod_cast hn
  have hlog : 0 ≤ log (1 / η) := Real.log_nonneg (by rw [le_div_iff₀ hη]; linarith)
  have harg : (0:ℝ) ≤ log (1 / η) / (2 * n) := by positivity
  have hsq : (B * √(log (1 / η) / (2 * n))) ^ 2 = B ^ 2 * (log (1 / η) / (2 * n)) := by
    rw [mul_pow, Real.sq_sqrt harg]
  rw [hsq]
  have hB2 : B ^ 2 ≠ 0 := by positivity
  have hstep : -2 * (n:ℝ) * (B ^ 2 * (log (1 / η) / (2 * n))) / B ^ 2 = -log (1 / η) := by
    field_simp
  rw [hstep, ← Real.log_inv, one_div, inv_inv, Real.exp_log hη]

/-- `ε₁` and `ε₂` of the proof are nonnegative, as Hoeffding's inequality requires. -/
theorem calibrated_nonneg {B η : ℝ} {n : ℕ} (hB : 0 ≤ B) :
    0 ≤ B * √(log (1 / η) / (2 * n)) :=
  mul_nonneg hB (Real.sqrt_nonneg _)

end TimeWarp
