import Std

def differences (a : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => differences a n + (a (n + 1) - a n)

theorem result (a : Nat → Int) (n : Nat) : differences a n = a n - a 0 := by
  induction n with
  | zero => simp [differences]
  | succ n ih => simp only [differences, ih]; omega

#print axioms result
