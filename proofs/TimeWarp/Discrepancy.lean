/-
Appendix, "A Theoretical Perspective on Multi-Version Training".

This file formalises Definition `def:discrepancy` (Eq. `eq:discrepancy`) together with the
three properties the paper asserts immediately after it -- "It is symmetric, vanishes for
`u = v`, and satisfies the triangle inequality" -- and the bound `disc ≤ B` implied by
Assumption `ass:bounded`.

Assumption `ass:bounded` has two halves: `0 ≤ ℓ(θ;h,y) ≤ B` and `Θ` finite. Finiteness enters
here as `[Finite Θ]`, which is what makes the supremum in Eq. `eq:discrepancy` finite.
Nonemptiness of `Θ` is left implicit in the paper; it is stated explicitly as `[Nonempty Θ]`
wherever it is needed.
-/
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Order.ConditionallyCompleteLattice.Finset
import Mathlib.Data.Set.Finite.Lattice

set_option linter.unusedSectionVars false

namespace TimeWarp

variable {V Θ : Type*}

/-- `disc_Θ(u,v) = sup_{θ ∈ Θ} |L_u(θ) - L_v(θ)|`, Eq. `eq:discrepancy`.

`L v θ` is the version risk `L_v(θ)` of Eq. `eq:versionRisk`; it is kept abstract here
because Proposition `prop:coverage` uses nothing else about it. -/
noncomputable def disc (L : V → Θ → ℝ) (u v : V) : ℝ := ⨆ θ : Θ, |L u θ - L v θ|

section Finite

variable [Finite Θ] (L : V → Θ → ℝ) (u v w : V)

/-- Finiteness of `Θ` (Assumption `ass:bounded`) makes the supremum in Eq. `eq:discrepancy`
a supremum over a finite set, hence finite. -/
theorem bddAbove_disc : BddAbove (Set.range fun θ : Θ => |L u θ - L v θ|) :=
  (Set.finite_range _).bddAbove

/-- Each policy's gap is at most the discrepancy. This is the only property of
Eq. `eq:discrepancy` used in the proof of Proposition `prop:coverage`. -/
theorem abs_le_disc (θ : Θ) : |L u θ - L v θ| ≤ disc L u v :=
  le_ciSup (bddAbove_disc L u v) θ

/-- The signed form of `abs_le_disc`: `L_u(θ) - L_v(θ) ≤ disc_Θ(u,v)`. -/
theorem sub_le_disc (θ : Θ) : L u θ - L v θ ≤ disc L u v :=
  (le_abs_self _).trans (abs_le_disc L u v θ)

/-- "... vanishes for `u = v`." -/
@[simp] theorem disc_self [Nonempty Θ] : disc L u u = 0 := by
  simp [disc]

/-- "It is symmetric." -/
theorem disc_comm : disc L u v = disc L v u :=
  iSup_congr fun _ => abs_sub_comm _ _

/-- The discrepancy is nonnegative. -/
theorem disc_nonneg [Nonempty Θ] : 0 ≤ disc L u v :=
  le_trans (abs_nonneg _) (abs_le_disc L u v (Classical.arbitrary Θ))

/-- "... and satisfies the triangle inequality." -/
theorem disc_triangle [Nonempty Θ] : disc L u w ≤ disc L u v + disc L v w := by
  refine ciSup_le fun θ => ?_
  calc |L u θ - L w θ| ≤ |L u θ - L v θ| + |L v θ - L w θ| := abs_sub_le _ _ _
    _ ≤ disc L u v + disc L v w := add_le_add (abs_le_disc L u v θ) (abs_le_disc L v w θ)

/-- Assumption `ass:bounded` bounds the discrepancy by `B`: if every version risk lies in
`[0, B]` then no two versions are further apart than `B`. -/
theorem disc_le_of_mem_Icc [Nonempty Θ] {B : ℝ} (h : ∀ x θ, L x θ ∈ Set.Icc (0:ℝ) B) :
    disc L u v ≤ B := by
  refine ciSup_le fun θ => ?_
  obtain ⟨hu0, huB⟩ := h u θ
  obtain ⟨hv0, hvB⟩ := h v θ
  rw [abs_sub_le_iff]
  constructor <;> linarith

end Finite

end TimeWarp
