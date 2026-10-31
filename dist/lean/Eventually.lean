import Std

theorem result (P Q : Nat → Prop)
    (hp : ∃ N, ∀ n, N ≤ n → P n) (hq : ∃ N, ∀ n, N ≤ n → Q n) :
    ∃ N, ∀ n, N ≤ n → P n ∧ Q n := by
  obtain ⟨A, hA⟩ := hp
  obtain ⟨B, hB⟩ := hq
  refine ⟨A + B, ?_⟩
  intro n hn
  exact ⟨hA n (by omega), hB n (by omega)⟩

#print axioms result
