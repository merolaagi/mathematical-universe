import Std

-- A named lemma can support more than one result.
theorem positive_implies_nonzero (n : Nat) (h : 0 < n) : n ≠ 0 := by
  omega

theorem successor_nonzero (n : Nat) : n + 1 ≠ 0 := by
  apply positive_implies_nonzero
  omega

theorem square_positive_input_nonzero (n : Nat) (h : 0 < n) : n * n ≠ 0 := by
  exact Nat.mul_ne_zero (positive_implies_nonzero n h) (positive_implies_nonzero n h)

#print axioms successor_nonzero
#print axioms square_positive_input_nonzero
