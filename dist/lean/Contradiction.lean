import Std

-- An elementary integer model of incompatible bounds.
-- This does NOT prove the manuscript's real-number limit estimates.
theorem incompatible_bounds (x lower upper : Int)
    (hLower : lower ≤ x) (hUpper : x ≤ upper)
    (hGap : upper < lower) : False := by
  omega

#print axioms incompatible_bounds
