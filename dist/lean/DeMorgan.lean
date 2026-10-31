import Std

theorem result (P Q : Prop) : ¬ (P ∨ Q) ↔ (¬ P ∧ ¬ Q) := by
  constructor
  · intro h
    exact ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩
  · intro h hor
    cases hor with
    | inl hp => exact h.1 hp
    | inr hq => exact h.2 hq

#print axioms result
