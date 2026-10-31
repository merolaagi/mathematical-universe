import Std

theorem result {α β : Type} (f : α → β) (g : β → α)
    (left : ∀ a, g (f a) = a) (a b : α) (h : f a = f b) : a = b := by
  have eq := congrArg g h
  simpa only [left] using eq

#print axioms result
