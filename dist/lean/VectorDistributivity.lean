import Std

def scale (k : Nat) (v : Nat × Nat) := (k * v.1, k * v.2)
def plus (u v : Nat × Nat) := (u.1 + v.1, u.2 + v.2)

theorem result (k : Nat) (u v : Nat × Nat) :
    scale k (plus u v) = plus (scale k u) (scale k v) := by
  simp [scale, plus, Nat.mul_add]

#print axioms result
