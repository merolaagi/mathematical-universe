import Std

theorem result {α β γ : Type} (f : α → β) (g : β → γ)
    (hf : ∀ b, ∃ a, f a = b) (hg : ∀ c, ∃ b, g b = c) :
    ∀ c, ∃ a, g (f a) = c := by
  intro c
  obtain ⟨b, hb⟩ := hg c
  obtain ⟨a, ha⟩ := hf b
  exact ⟨a, by rw [ha, hb]⟩

#print axioms result
