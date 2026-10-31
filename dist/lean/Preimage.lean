import Std

def preimage {α β : Type} (f : α → β) (S : β → Prop) : α → Prop :=
  fun x => S (f x)

theorem result {α β : Type} (f : α → β) (A B : β → Prop) (x : α) :
    preimage f (fun y => A y ∧ B y) x ↔ (preimage f A x ∧ preimage f B x) := by
  rfl

#print axioms result
