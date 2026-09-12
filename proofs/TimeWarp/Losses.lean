/-
The relation between the two behaviour-cloning losses of the paper:

* Eq. `eq:vanillaBCLoss`, `L_BC(θ) = -E[log π_θ(a|h)]` with `a = φ(y)`, and
* Eq. `eq:timewarpBC`,   `L_TW-BC(θ) = -E[log π_θ(y|h)]`.

§`sec:timewarpBC` introduces the second with "The standard BC loss (Eq. `eq:vanillaBCLoss`)
can be reformulated as", which reads as an identity. It is not one: the action probability is
the *marginal* of the response probability over the fibre of the parser `φ`, so

  `π_θ(a|h) = Σ_{y' : φ(y') = a} π_θ(y'|h) ≥ π_θ(y|h)`,

and therefore `L_BC(θ) ≤ L_TW-BC(θ)` pointwise, with equality exactly when the response
distribution puts no mass on any other response with the same action. The two objectives
coincide only in that degenerate case; in general they differ, which is the whole point of
the section ("we train web agents on the full teacher-agent response rather than only on
action tokens").
-/
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset

set_option linter.unusedSectionVars false

namespace TimeWarp

open Real

variable {Y A : Type*} [Fintype Y] [DecidableEq Y] [DecidableEq A]

/-- The fibre of the parser over an action: the responses `y'` with `φ(y') = a`. -/
def fibre (φ : Y → A) (a : A) : Finset Y := Finset.univ.filter fun y => φ y = a

@[simp] theorem mem_fibre {φ : Y → A} {y : Y} {a : A} : y ∈ fibre φ a ↔ φ y = a := by
  simp [fibre]

/-- `π_θ(a|h) = Σ_{y' : φ(y') = a} π_θ(y'|h)`: the action probability is the marginal of the
response probability over the fibre of the parser. -/
noncomputable def actionProb (φ : Y → A) (π : Y → ℝ) (a : A) : ℝ := ∑ y ∈ fibre φ a, π y

variable {φ : Y → A} {π : Y → ℝ}

/-- The response probability of `y` is at most the action probability of `φ(y)`. -/
theorem prob_le_actionProb (φ : Y → A) (hπ : ∀ y, 0 ≤ π y) (y : Y) :
    π y ≤ actionProb φ π (φ y) :=
  Finset.single_le_sum (f := π) (fun z _ => hπ z) (by simp)

/-- Equality holds exactly when no other response shares the action of `y`, i.e. when the
non-action tokens carry no probability mass of their own. -/
theorem prob_eq_actionProb_iff (φ : Y → A) (hπ : ∀ y, 0 ≤ π y) (y : Y) :
    π y = actionProb φ π (φ y) ↔ ∀ z, φ z = φ y → z ≠ y → π z = 0 := by
  have hmem : y ∈ fibre φ (φ y) := by simp
  rw [actionProb, ← Finset.sum_erase_add _ _ hmem]
  constructor
  · intro h z hz hne
    have hsum : ∑ x ∈ (fibre φ (φ y)).erase y, π x = 0 := by linarith
    have hzmem : z ∈ (fibre φ (φ y)).erase y := by simp [Finset.mem_erase, hne, hz]
    have hle := Finset.single_le_sum (f := π) (fun w _ => hπ w) hzmem
    rw [hsum] at hle
    exact le_antisymm hle (hπ z)
  · intro h
    have hsum : ∑ x ∈ (fibre φ (φ y)).erase y, π x = 0 :=
      Finset.sum_eq_zero fun z hz => by
        rw [Finset.mem_erase] at hz
        exact h z (by simpa using hz.2) hz.1
    rw [hsum, zero_add]

/-- **`L_BC ≤ L_TW-BC` pointwise.** The action-only negative log-likelihood of
Eq. `eq:vanillaBCLoss` never exceeds the full-response one of Eq. `eq:timewarpBC`. -/
theorem bcLoss_le_twbcLoss (φ : Y → A) (hπ : ∀ y, 0 ≤ π y) (y : Y) (hy : 0 < π y) :
    -log (actionProb φ π (φ y)) ≤ -log (π y) :=
  neg_le_neg (Real.log_le_log hy (prob_le_actionProb φ hπ y))

/-- **The two losses are not the same objective.** With two responses sharing one action and
half the mass each, the action-only loss is `0` and the full-response loss is `log 2`.
So Eq. `eq:vanillaBCLoss` is not a reformulation of Eq. `eq:timewarpBC`. -/
theorem bcLoss_lt_twbcLoss_example :
    ∃ (φ : Bool → Unit) (π : Bool → ℝ) (y : Bool),
      (∀ y, 0 ≤ π y) ∧ (∑ y, π y) = 1 ∧
      -log (actionProb φ π (φ y)) < -log (π y) := by
  refine ⟨fun _ => (), fun _ => 1/2, true, fun _ => by norm_num, by norm_num, ?_⟩
  have hA : actionProb (fun _ : Bool => ()) (fun _ => (1:ℝ)/2) () = 1 := by
    simp [actionProb, fibre]
  rw [hA, Real.log_one, neg_zero, neg_pos]
  have : Real.log (1/2) < 0 := Real.log_neg (by norm_num) (by norm_num)
  linarith

end TimeWarp
