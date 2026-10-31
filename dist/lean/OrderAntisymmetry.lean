import Std

theorem result (a b : Int) (h₁ : a ≤ b) (h₂ : b ≤ a) : a = b := by
  omega

#print axioms result
