import Std

-- Each hypothesis is explicit: this proves the composition, not P itself.
theorem compose_steps (P Q R : Prop)
    (first : P → Q) (second : Q → R) : P → R := by
  intro proofOfP
  have proofOfQ : Q := first proofOfP
  exact second proofOfQ

#print axioms compose_steps
