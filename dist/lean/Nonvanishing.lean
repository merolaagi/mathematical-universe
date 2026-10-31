import Std

-- none models an infinite valuation; some k models a finite valuation.
-- Establishing the hypothesis finiteVal for a determinant is separate work.
theorem nonzero_of_finite_value {α : Type} (zero : α)
    (valuation : α → Option Int) (atZero : valuation zero = none)
    (q : α) (k : Int) (finiteVal : valuation q = some k) : q ≠ zero := by
  intro equalsZero
  rw [equalsZero, atZero] at finiteVal
  contradiction

#print axioms nonzero_of_finite_value
