import Std

inductive Reach {α : Type} (edge : α → α → Prop) : α → α → Prop where
  | refl (a) : Reach edge a a
  | step {a b c} : edge a b → Reach edge b c → Reach edge a c

theorem result {α : Type} {edge : α → α → Prop} {a b c : α}
    (ab : Reach edge a b) (bc : Reach edge b c) : Reach edge a c := by
  induction ab with
  | refl => exact bc
  | step e path ih => exact Reach.step e (ih bc)

#print axioms result
