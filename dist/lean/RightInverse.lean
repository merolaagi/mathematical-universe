import Std

theorem result {α β : Type} (f : α → β) (g : β → α)
    (right : ∀ b, f (g b) = b) : ∀ b, ∃ a, f a = b := by
  intro b
  exact ⟨g b, right b⟩

#print axioms result
