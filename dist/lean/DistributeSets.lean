import Std

theorem result {α : Type} (A B C : α → Prop) (x : α) :
    (A x ∧ (B x ∨ C x)) ↔ ((A x ∧ B x) ∨ (A x ∧ C x)) := by
  constructor
  · intro h
    cases h.2 with
    | inl hb => exact Or.inl ⟨h.1, hb⟩
    | inr hc => exact Or.inr ⟨h.1, hc⟩
  · intro h
    cases h with
    | inl hab => exact ⟨hab.1, Or.inl hab.2⟩
    | inr hac => exact ⟨hac.1, Or.inr hac.2⟩

#print axioms result
