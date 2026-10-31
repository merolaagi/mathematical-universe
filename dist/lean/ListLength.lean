import Std

theorem result {α : Type} (xs ys : List α) : (xs ++ ys).length = xs.length + ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp [ih, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]

#print axioms result
