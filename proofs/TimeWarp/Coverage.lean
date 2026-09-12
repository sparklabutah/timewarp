/-
Appendix, "A Theoretical Perspective on Multi-Version Training", §`sec:theoryCoverage`.

Proposition `prop:coverage` (Eq. `eq:coverageBound`) and its proof, plus the monotonicity
claim that follows the statement, plus two formal counterexamples recording the two places
where the printed statement/takeaway says slightly more than is true.

The set of training versions `V_tr` is a `Finset V` and `k = V_tr.card`.
-/
import TimeWarp.Discrepancy
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Field

set_option linter.unusedSectionVars false

namespace TimeWarp

variable {V Θ : Type*} [Finite Θ] [Nonempty Θ]

/-! ### The two inequalities of Eq. `eq:coverageBound` -/

/-- First inequality of Eq. `eq:coverageBound`:
`L_u(θ) ≤ min_{v ∈ V_tr} { L_v(θ) + disc_Θ(u,v) }`.

Proof of the paper: "By Definition `def:discrepancy`, `L_u(θ) - L_v(θ) ≤ disc_Θ(u,v)` for every
`v ∈ V_tr`, which gives the first inequality after taking the minimum over `v`." -/
theorem coverage_le_min (L : V → Θ → ℝ) (u : V) (θ : Θ)
    (Vtr : Finset V) (hne : Vtr.Nonempty) :
    L u θ ≤ Vtr.inf' hne (fun v => L v θ + disc L u v) :=
  Finset.le_inf' hne _ fun v _ => by have := sub_le_disc L u v θ; linarith

/-- "A minimum is at most an average." -/
theorem inf'_le_average (Vtr : Finset V) (hne : Vtr.Nonempty) (f : V → ℝ) :
    Vtr.inf' hne f ≤ (∑ v ∈ Vtr, f v) / Vtr.card := by
  have hcard : (0:ℝ) < Vtr.card := by
    exact_mod_cast Finset.card_pos.2 hne
  rw [le_div_iff₀ hcard]
  have h : Vtr.card • Vtr.inf' hne f ≤ ∑ v ∈ Vtr, f v :=
    Finset.card_nsmul_le_sum _ _ _ fun v hv => Finset.inf'_le _ hv
  rw [nsmul_eq_mul] at h
  linarith

/-- Second inequality of Eq. `eq:coverageBound`: the minimum is at most the average, so
`L_u(θ) ≤ (1/k) Σ_v L_v(θ) + (1/k) Σ_v disc_Θ(u,v)`. -/
theorem coverage_le_average (L : V → Θ → ℝ) (u : V) (θ : Θ)
    (Vtr : Finset V) (hne : Vtr.Nonempty) :
    Vtr.inf' hne (fun v => L v θ + disc L u v)
      ≤ (∑ v ∈ Vtr, L v θ) / Vtr.card + (∑ v ∈ Vtr, disc L u v) / Vtr.card := by
  refine (inf'_le_average Vtr hne _).trans_eq ?_
  rw [Finset.sum_add_distrib, add_div]

/-- **Proposition `prop:coverage`**, the full chain of Eq. `eq:coverageBound`.

The hypothesis `V_tr ≠ ∅` is *not* stated in the paper; see `coverage_empty_false` for why it
is needed. -/
theorem coverage (L : V → Θ → ℝ) (u : V) (θ : Θ) (Vtr : Finset V) (hne : Vtr.Nonempty) :
    L u θ ≤ Vtr.inf' hne (fun v => L v θ + disc L u v) ∧
    Vtr.inf' hne (fun v => L v θ + disc L u v)
      ≤ (∑ v ∈ Vtr, L v θ) / Vtr.card + (∑ v ∈ Vtr, disc L u v) / Vtr.card :=
  ⟨coverage_le_min L u θ Vtr hne, coverage_le_average L u θ Vtr hne⟩

/-- "The middle expression is non-increasing in `V_tr` with respect to set inclusion."
Adding a training version can only tighten the bound. -/
theorem coverage_min_antitone (L : V → Θ → ℝ) (u : V) (θ : Θ)
    {Vtr Vtr' : Finset V} (hsub : Vtr ⊆ Vtr') (hne : Vtr.Nonempty) :
    Vtr'.inf' (hne.mono hsub) (fun v => L v θ + disc L u v)
      ≤ Vtr.inf' hne (fun v => L v θ + disc L u v) :=
  Finset.le_inf' hne _ fun _ hv => Finset.inf'_le _ (hsub hv)

/-- "... and adding one close to `u` tightens it most": a training version at discrepancy `0`
from `u` reduces the bound to `L_u(θ)` itself, which is the best possible value. -/
theorem coverage_min_eq_of_mem (L : V → Θ → ℝ) (u : V) (θ : Θ)
    (Vtr : Finset V) (hne : Vtr.Nonempty) (hu : u ∈ Vtr) :
    Vtr.inf' hne (fun v => L v θ + disc L u v) = L u θ :=
  le_antisymm
    (by
      have h := Finset.inf'_le (fun v => L v θ + disc L u v) hu
      rwa [disc_self, add_zero] at h)
    (coverage_le_min L u θ Vtr hne)

/-! ### Two things the printed statement says that are not quite true -/

/-- **Discrepancy 1.** Proposition `prop:coverage` is stated for "every set of training
versions `V_tr`", with no nonemptiness hypothesis, while the right-most expression of
Eq. `eq:coverageBound` divides by `k = |V_tr|`. For `V_tr = ∅` both quotients read `0/0`,
which Lean (like the usual convention) evaluates to `0`, and the inequality is then false. -/
theorem coverage_empty_false :
    ¬ (∀ (V Θ : Type) (_ : Finite Θ) (_ : Nonempty Θ) (L : V → Θ → ℝ) (u : V) (θ : Θ)
         (Vtr : Finset V),
        L u θ ≤ (∑ v ∈ Vtr, L v θ) / Vtr.card + (∑ v ∈ Vtr, disc L u v) / Vtr.card) := by
  intro h
  have := h Unit Unit inferInstance inferInstance (fun _ _ => (1:ℝ)) () () ∅
  norm_num at this

/-- **Discrepancy 2.** The monotonicity claim is made, correctly, for the *middle* expression
of Eq. `eq:coverageBound`. It does not carry over to the right-most expression: the averaged
bound can strictly increase when a training version is added. Here `V = Bool`, `u = false`,
`L false = 0`, `L true = 10`; the bound for `V_tr = {false}` is `0` and for
`V_tr = {false, true}` it is `10`.

This matters for reading the takeaway, which pairs "adding a training version can only tighten
the bound" with the right-most expression in the next sentence. -/
theorem coverage_average_not_antitone :
    ∃ (L : Bool → Unit → ℝ) (u : Bool) (θ : Unit) (Vtr Vtr' : Finset Bool),
      Vtr ⊆ Vtr' ∧
      (∑ v ∈ Vtr, L v θ) / Vtr.card + (∑ v ∈ Vtr, disc L u v) / Vtr.card
        < (∑ v ∈ Vtr', L v θ) / Vtr'.card + (∑ v ∈ Vtr', disc L u v) / Vtr'.card := by
  classical
  refine ⟨fun v _ => if v then 10 else 0, false, (), {false}, {false, true}, by decide, ?_⟩
  have hdisc : ∀ v : Bool, disc (fun v (_ : Unit) => if v then (10:ℝ) else 0) false v
      = |(if false then (10:ℝ) else 0) - (if v then (10:ℝ) else 0)| := by
    intro v; simp [disc]
  simp [hdisc]

end TimeWarp
