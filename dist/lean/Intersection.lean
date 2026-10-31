import Std

theorem result {α : Type} (A B : α → Prop) (x : α) :
    (A x ∧ B x) ↔ (B x ∧ A x) := by
  constructor
  · intro h; exact ⟨h.2, h.1⟩
  · intro h; exact ⟨h.2, h.1⟩

#print axioms result
