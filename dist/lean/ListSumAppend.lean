import Std

def total : List Nat → Nat
  | [] => 0
  | x :: xs => x + total xs

theorem result (xs ys : List Nat) : total (xs ++ ys) = total xs + total ys := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, ih, Nat.add_assoc]

#print axioms result
