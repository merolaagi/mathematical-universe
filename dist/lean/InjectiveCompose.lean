import Std

theorem result {α β γ : Type} (f : α → β) (g : β → γ)
    (hf : ∀ a b, f a = f b → a = b)
    (hg : ∀ a b, g a = g b → a = b) :
    ∀ a b, g (f a) = g (f b) → a = b := by
  intro a b h
  exact hf a b (hg (f a) (f b) h)

#print axioms result
