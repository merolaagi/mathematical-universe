import Std

theorem result (f : Int → Int) (additive : ∀ a b, f (a + b) = f a + f b)
    (x y : Int) (hx : f x = 0) (hy : f y = 0) : f (x + y) = 0 := by
  rw [additive, hx, hy]
  rfl

#print axioms result
