import Std

theorem result (P Q : Prop) (h : P → Q) : ¬ Q → ¬ P := by
  intro notQ proofP
  exact notQ (h proofP)

#print axioms result
