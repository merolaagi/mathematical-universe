import Std

theorem result {α : Type} (A B C : α → Prop) (x : α) :
    ((A x ∨ B x) ∨ C x) ↔ (A x ∨ (B x ∨ C x)) := by
  simp only [or_assoc]

#print axioms result
