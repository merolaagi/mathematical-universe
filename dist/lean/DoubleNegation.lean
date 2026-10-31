import Std

theorem result (P : Prop) : (¬ ¬ P) → P := by
  classical
  intro h
  by_cases hp : P
  · exact hp
  · exact False.elim (h hp)

#print axioms result
