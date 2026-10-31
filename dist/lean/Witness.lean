import Std

theorem result (n : Nat) : ∃ m : Nat, n < m := by
  exact ⟨n + 1, by omega⟩

#print axioms result
