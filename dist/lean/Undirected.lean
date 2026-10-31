import Std

theorem result {α : Type} (edge : α → α → Prop)
    (symmetric : ∀ a b, edge a b → edge b a) (a b c : α)
    (ab : edge a b) (bc : edge b c) : edge c b ∧ edge b a := by
  exact ⟨symmetric b c bc, symmetric a b ab⟩

#print axioms result
