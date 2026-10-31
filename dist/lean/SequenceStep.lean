import Std

theorem result (a : Nat → Int) (h : ∀ n, a n ≤ a (n + 1)) (n k : Nat) :
    a n ≤ a (n + k) := by
  induction k with
  | zero => simp
  | succ k ih =>
    have hs := h (n + k)
    have ht : a n ≤ a ((n + k) + 1) := by omega
    simpa only [Nat.add_assoc] using ht

#print axioms result
