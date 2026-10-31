import Std

theorem result {α : Type} (a : Nat → α) (h : ∀ n, a (n + 1) = a n) (n : Nat) :
    a n = a 0 := by
  induction n with
  | zero => rfl
  | succ n ih => exact (h n).trans ih

#print axioms result
