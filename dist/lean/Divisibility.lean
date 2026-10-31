import Std

theorem result (a b c : Nat) (hab : ∃ k, b = a * k)
    (hbc : ∃ k, c = b * k) : ∃ k, c = a * k := by
  obtain ⟨k, hk⟩ := hab
  obtain ⟨l, hl⟩ := hbc
  exact ⟨k * l, by rw [hl, hk, Nat.mul_assoc]⟩

#print axioms result
