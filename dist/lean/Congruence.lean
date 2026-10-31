import Std

theorem result (a b c d m : Int)
    (hab : ∃ k, a - b = m * k) (hcd : ∃ k, c - d = m * k) :
    ∃ k, (a + c) - (b + d) = m * k := by
  obtain ⟨k, hk⟩ := hab
  obtain ⟨l, hl⟩ := hcd
  refine ⟨k + l, ?_⟩
  rw [Int.mul_add]
  omega

#print axioms result
