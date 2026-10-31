import Std

theorem result (a b c d : Int) (ab : a ≤ b) (bc : b ≤ c) (cd : c ≤ d) : a ≤ d := by
  omega

#print axioms result
