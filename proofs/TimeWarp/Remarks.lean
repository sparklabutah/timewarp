/-
Remark `rem:versionCountBridge` ("What Proposition `prop:versionCount` predicts") and the
monotonicity part of Remark `rem:coverageBridge`.

The two predictions of `rem:versionCountBridge` are statements about `ε₁` and `ε₂`:

(i)  with `k = 1` the across-version term equals `B √(log(4|Θ|/δ)/2)` and does not involve `M`,
     so no number of extra trajectories from the same version drives the bound to `0`;
(ii) a fixed budget `kM` spread over more versions leaves the within-version term unchanged and
     shrinks the across-version term.

The rest of the remark ("relating the two requires the standard imitation-learning argument",
"the i.i.d. assumption on versions is an idealization") is commentary, not a claim to prove.
-/
import TimeWarp.VersionCount

set_option linter.unusedSectionVars false

namespace TimeWarp

open Real

variable {B δ : ℝ} {n k M : ℕ}

/-! ### Prediction (i): a single training version -/

/-- With `k = 1` the across-version term is `B √(log(4|Θ|/δ)/2)`, exactly as the remark says. -/
theorem eps1_one : eps1 B δ n 1 = B * √(log (4 * n / δ) / 2) := by
  simp [eps1]

-- `eps1` has no `M` argument at all: the across-version term cannot depend on the number of
-- pairs drawn per version. The consequence the remark draws is `single_version_floor` below.

/-- `ε₁ > 0` whenever the bound is non-vacuous (`δ < 4|Θ|`, which holds for `δ < 1 ≤ |Θ|`). -/
theorem eps1_pos (hB : 0 < B) (hk : 0 < k) (hδ0 : 0 < δ) (hδ : δ < 4 * n) :
    0 < eps1 B δ n k := by
  have hk0 : (0:ℝ) < k := by exact_mod_cast hk
  have hlog : 0 < log (4 * n / δ) := Real.log_pos (by rw [lt_div_iff₀ hδ0]; linarith)
  have : 0 < log (4 * (n:ℝ) / δ) / (2 * k) := by positivity
  exact mul_pos hB (Real.sqrt_pos.2 this)

/-- Prediction (i): with a single training version the guarantee of Eq. `eq:versionCountBound`
can never be tightened past `ε₁ > 0`, however many pairs `M` are added. -/
theorem single_version_floor (hB : 0 < B) (hδ0 : 0 < δ) (hδ : δ < 4 * n) (M : ℕ) :
    0 < eps1 B δ n 1 ∧ eps1 B δ n 1 ≤ eps2 B δ n 1 M + eps1 B δ n 1 :=
  ⟨eps1_pos hB one_pos hδ0 hδ, le_add_of_nonneg_left (eps2_nonneg hB.le)⟩

/-! ### Prediction (ii): a fixed budget spread over more versions -/

/-- The within-version term depends on `k` and `M` only through the total number of pairs `kM`,
so redistributing a fixed budget leaves it unchanged. -/
theorem eps2_of_budget {k₁ M₁ k₂ M₂ : ℕ} (h : k₁ * M₁ = k₂ * M₂) :
    eps2 B δ n k₁ M₁ = eps2 B δ n k₂ M₂ := by
  have hc : ((k₁ : ℝ) * (M₁ : ℝ)) = (k₂ : ℝ) * (M₂ : ℝ) := by exact_mod_cast h
  simp only [eps2, hc]

/-- The across-version term is non-increasing in the number of training versions. -/
theorem eps1_antitone (hB : 0 ≤ B) (hδ0 : 0 < δ) (hδ : δ ≤ 4 * n) {k₁ k₂ : ℕ}
    (hk₁ : 0 < k₁) (h : k₁ ≤ k₂) :
    eps1 B δ n k₂ ≤ eps1 B δ n k₁ := by
  have hk₁0 : (0:ℝ) < k₁ := by exact_mod_cast hk₁
  have hk₂0 : (0:ℝ) < k₂ := by exact_mod_cast lt_of_lt_of_le hk₁ h
  have hle : (k₁:ℝ) ≤ k₂ := by exact_mod_cast h
  have hlog : 0 ≤ log (4 * (n:ℝ) / δ) :=
    Real.log_nonneg (by rw [le_div_iff₀ hδ0]; linarith)
  have harg : log (4 * (n:ℝ) / δ) / (2 * k₂) ≤ log (4 * (n:ℝ) / δ) / (2 * k₁) :=
    div_le_div_of_nonneg_left hlog (by positivity) (by linarith)
  exact mul_le_mul_of_nonneg_left (Real.sqrt_le_sqrt harg) hB

/-- Prediction (ii) in full: moving a fixed budget of `kM` pairs from few versions to many
leaves the within-version term alone and can only shrink the across-version term. -/
theorem fixed_budget (hB : 0 ≤ B) (hδ0 : 0 < δ) (hδ : δ ≤ 4 * n) {k₁ M₁ k₂ M₂ : ℕ}
    (hbudget : k₁ * M₁ = k₂ * M₂) (hk₁ : 0 < k₁) (hk : k₁ ≤ k₂) :
    eps2 B δ n k₂ M₂ = eps2 B δ n k₁ M₁ ∧ eps1 B δ n k₂ ≤ eps1 B δ n k₁ :=
  ⟨(eps2_of_budget hbudget).symm, eps1_antitone hB hδ0 hδ hk₁ hk⟩

end TimeWarp
