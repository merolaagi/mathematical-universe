import Std

theorem result {α : Type} (x : α) : (none : Option α) ≠ some x := by
  intro h
  cases h

#print axioms result
