import Std

theorem result (n : Nat) : n % 2 = 0 ∨ n % 2 = 1 := by
  omega

#print axioms result
