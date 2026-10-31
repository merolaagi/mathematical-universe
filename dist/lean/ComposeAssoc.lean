import Std

theorem result {α β γ δ : Type} (f : α → β) (g : β → γ) (h : γ → δ) :
    (fun x => h (g (f x))) = (fun x => (fun y => h (g y)) (f x)) := by
  rfl

#print axioms result
