import Std

theorem result (a b : Nat) (ha : ∃ k, a = 2 * k)
    (hb : ∃ k, b = 2 * k) : ∃ k, a + b = 2 * k := by
  obtain ⟨k, hk⟩ := ha
  obtain ⟨l, hl⟩ := hb
  exact ⟨k + l, by rw [hk, hl, Nat.mul_add]⟩

#print axioms result
