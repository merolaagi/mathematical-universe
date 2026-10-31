import Std

theorem result {α β γ : Type} (f : α → β) (g : β → γ) (xs : List α) :
    (xs.map f).map g = xs.map (fun x => g (f x)) := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons, ih]

#print axioms result
