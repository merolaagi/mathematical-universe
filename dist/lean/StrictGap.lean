import Std

theorem result (a b : Int) (h : a + 1 ≤ b) : a ≠ b := by
  omega

#print axioms result
