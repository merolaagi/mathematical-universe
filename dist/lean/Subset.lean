import Std

theorem result {α : Type} (A B C : α → Prop)
    (ab : ∀ x, A x → B x) (bc : ∀ x, B x → C x) : ∀ x, A x → C x := by
  intro x hx
  exact bc x (ab x hx)

#print axioms result
