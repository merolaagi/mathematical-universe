import Std

theorem result (P Q : Prop) : (P ∧ Q) ↔ (Q ∧ P) := by
  constructor
  · intro h; exact ⟨h.2, h.1⟩
  · intro h; exact ⟨h.2, h.1⟩

#print axioms result
