"""Maintained standalone Lean examples. Run check_lean_examples.py after generation."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'dist';rows=[]
def add(id,title,category,ids,scope,code):
 rows.append(dict(id=id,title=title,category=category,nodeIds=ids,scope=scope))
 (R/'lean'/f'{id}.lean').write_text('import Std\n\n'+code.strip()+'\n\n#print axioms result\n')
add('AndComm','Conjunction: rearrange two assumptions','Logic',['concept:logic'],'An exact propositional equivalence; no mathematical premises are supplied implicitly.', '''
theorem result (P Q : Prop) : (P ∧ Q) ↔ (Q ∧ P) := by
  constructor
  · intro h; exact ⟨h.2, h.1⟩
  · intro h; exact ⟨h.2, h.1⟩
''')
add('OrComm','Disjunction: reason by cases','Logic',['concept:logic'],'An exact propositional equivalence proved by considering both cases.', '''
theorem result (P Q : Prop) : (P ∨ Q) ↔ (Q ∨ P) := by
  constructor
  · intro h
    cases h with
    | inl hp => exact Or.inr hp
    | inr hq => exact Or.inl hq
  · intro h
    cases h with
    | inl hq => exact Or.inr hq
    | inr hp => exact Or.inl hp
''')
add('Contrapositive','Contrapositive of an implication','Logic',['concept:contradiction','concept:logic'],'Proves the forward contraposition rule constructively.', '''
theorem result (P Q : Prop) (h : P → Q) : ¬ Q → ¬ P := by
  intro notQ proofP
  exact notQ (h proofP)
''')
add('DoubleNegation','Classical proof by contradiction','Logic',['concept:contradiction'],'Double-negation elimination uses classical reasoning; inspect the printed dependencies.', '''
theorem result (P : Prop) : (¬ ¬ P) → P := by
  classical
  intro h
  by_cases hp : P
  · exact hp
  · exact False.elim (h hp)
''')
add('DeMorgan','Negating a disjunction','Logic',['concept:logic','concept:contradiction'],'This De Morgan law is constructive.', '''
theorem result (P Q : Prop) : ¬ (P ∨ Q) ↔ (¬ P ∧ ¬ Q) := by
  constructor
  · intro h
    exact ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩
  · intro h hor
    cases hor with
    | inl hp => exact h.1 hp
    | inr hq => exact h.2 hq
''')
add('Witness','Existence requires a witness','Logic',['concept:logic','concept:integers'],'Produces a concrete natural-number witness for a universally quantified existence statement.', '''
theorem result (n : Nat) : ∃ m : Nat, n < m := by
  exact ⟨n + 1, by omega⟩
''')
add('Intersection','Set intersection is commutative','Sets',['concept:sets'],'Sets are predicates α → Prop; the conclusion is pointwise membership equivalence.', '''
theorem result {α : Type} (A B : α → Prop) (x : α) :
    (A x ∧ B x) ↔ (B x ∧ A x) := by
  constructor
  · intro h; exact ⟨h.2, h.1⟩
  · intro h; exact ⟨h.2, h.1⟩
''')
add('Union','Set union is associative','Sets',['concept:sets'],'Pointwise associativity for predicate-based sets.', '''
theorem result {α : Type} (A B C : α → Prop) (x : α) :
    ((A x ∨ B x) ∨ C x) ↔ (A x ∨ (B x ∨ C x)) := by
  simp only [or_assoc]
''')
add('DistributeSets','Intersection distributes over union','Sets',['concept:sets'],'An exact membership equivalence; the hypotheses describe membership in three sets.', '''
theorem result {α : Type} (A B C : α → Prop) (x : α) :
    (A x ∧ (B x ∨ C x)) ↔ ((A x ∧ B x) ∨ (A x ∧ C x)) := by
  constructor
  · intro h
    cases h.2 with
    | inl hb => exact Or.inl ⟨h.1, hb⟩
    | inr hc => exact Or.inr ⟨h.1, hc⟩
  · intro h
    cases h with
    | inl hab => exact ⟨hab.1, Or.inl hab.2⟩
    | inr hac => exact ⟨hac.1, Or.inr hac.2⟩
''')
add('Subset','Subset relations compose','Sets',['concept:sets','concept:functions'],'Uses the pointwise definition of subset inclusion.', '''
theorem result {α : Type} (A B C : α → Prop)
    (ab : ∀ x, A x → B x) (bc : ∀ x, B x → C x) : ∀ x, A x → C x := by
  intro x hx
  exact bc x (ab x hx)
''')
add('Preimage','Preimages preserve intersections','Sets',['concept:sets','concept:functions'],'The preimage membership identity reduces to definitions.', '''
def preimage {α β : Type} (f : α → β) (S : β → Prop) : α → Prop :=
  fun x => S (f x)

theorem result {α β : Type} (f : α → β) (A B : β → Prop) (x : α) :
    preimage f (fun y => A y ∧ B y) x ↔ (preimage f A x ∧ preimage f B x) := by
  rfl
''')
add('InjectiveCompose','Composition preserves injectivity','Functions',['concept:functions'],'Injectivity is stated explicitly as an equality implication.', '''
theorem result {α β γ : Type} (f : α → β) (g : β → γ)
    (hf : ∀ a b, f a = f b → a = b)
    (hg : ∀ a b, g a = g b → a = b) :
    ∀ a b, g (f a) = g (f b) → a = b := by
  intro a b h
  exact hf a b (hg (f a) (f b) h)
''')
add('SurjectiveCompose','Composition preserves surjectivity','Functions',['concept:functions'],'Surjectivity is proved by constructing preimages in reverse order.', '''
theorem result {α β γ : Type} (f : α → β) (g : β → γ)
    (hf : ∀ b, ∃ a, f a = b) (hg : ∀ c, ∃ b, g b = c) :
    ∀ c, ∃ a, g (f a) = c := by
  intro c
  obtain ⟨b, hb⟩ := hg c
  obtain ⟨a, ha⟩ := hf b
  exact ⟨a, by rw [ha, hb]⟩
''')
add('LeftInverse','A left inverse forces injectivity','Functions',['concept:functions','concept:linear'],'An elementary function theorem, not a proof that a particular matrix has an inverse.', '''
theorem result {α β : Type} (f : α → β) (g : β → α)
    (left : ∀ a, g (f a) = a) (a b : α) (h : f a = f b) : a = b := by
  have eq := congrArg g h
  simpa only [left] using eq
''')
add('RightInverse','A right inverse forces surjectivity','Functions',['concept:functions'],'A right inverse supplies the required witness directly.', '''
theorem result {α β : Type} (f : α → β) (g : β → α)
    (right : ∀ b, f (g b) = b) : ∀ b, ∃ a, f a = b := by
  intro b
  exact ⟨g b, right b⟩
''')
add('ComposeAssoc','Function composition is associative','Functions',['concept:functions','college:matmul'],'A pointwise composition identity. It does not certify a matrix algorithm.', '''
theorem result {α β γ δ : Type} (f : α → β) (g : β → γ) (h : γ → δ) :
    (fun x => h (g (f x))) = (fun x => (fun y => h (g y)) (f x)) := by
  rfl
''')
add('Divisibility','Divisibility is transitive','Arithmetic',['concept:integers','concept:prime'],'Uses a divides b as existence of a natural-number multiplier.', '''
theorem result (a b c : Nat) (hab : ∃ k, b = a * k)
    (hbc : ∃ k, c = b * k) : ∃ k, c = a * k := by
  obtain ⟨k, hk⟩ := hab
  obtain ⟨l, hl⟩ := hbc
  exact ⟨k * l, by rw [hl, hk, Nat.mul_assoc]⟩
''')
add('EvenSum','The sum of two even numbers is even','Arithmetic',['concept:integers'],'Evenness is expressed by an explicit natural-number witness.', '''
theorem result (a b : Nat) (ha : ∃ k, a = 2 * k)
    (hb : ∃ k, b = 2 * k) : ∃ k, a + b = 2 * k := by
  obtain ⟨k, hk⟩ := ha
  obtain ⟨l, hl⟩ := hb
  exact ⟨k + l, by rw [hk, hl, Nat.mul_add]⟩
''')
add('Congruence','Adding congruences modulo a fixed number','Arithmetic',['concept:modular'],'Congruence over integers is defined by the difference being an integer multiple.', '''
theorem result (a b c d m : Int)
    (hab : ∃ k, a - b = m * k) (hcd : ∃ k, c - d = m * k) :
    ∃ k, (a + c) - (b + d) = m * k := by
  obtain ⟨k, hk⟩ := hab
  obtain ⟨l, hl⟩ := hcd
  refine ⟨k + l, ?_⟩
  rw [Int.mul_add]
  omega
''')
add('Parity','Every natural number has parity zero or one','Arithmetic',['concept:modular','concept:integers'],'The remainder modulo two has exactly two possibilities.', '''
theorem result (n : Nat) : n % 2 = 0 ∨ n % 2 = 1 := by
  omega
''')
add('ListSumAppend','A finite sum splits over concatenation','Finite structures',['reason:deep:finite-distribution','concept:counting'],'A recursive natural-number list sum, proved by structural induction.', '''
def total : List Nat → Nat
  | [] => 0
  | x :: xs => x + total xs

theorem result (xs ys : List Nat) : total (xs ++ ys) = total xs + total ys := by
  induction xs with
  | nil => simp [total]
  | cons x xs ih => simp [total, ih, Nat.add_assoc]
''')
add('ListLength','Concatenation adds list lengths','Finite structures',['concept:counting','concept:induction'],'An exact statement about finite lists of arbitrary element type.', '''
theorem result {α : Type} (xs ys : List α) : (xs ++ ys).length = xs.length + ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp [ih, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
''')
add('ListMap','Mapping twice equals mapping a composition','Finite structures',['concept:functions','concept:induction'],'Structural induction establishes a useful finite-data transformation law.', '''
theorem result {α β γ : Type} (f : α → β) (g : β → γ) (xs : List α) :
    (xs.map f).map g = xs.map (fun x => g (f x)) := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons, ih]
''')
add('Telescoping','A telescoping finite sum','Finite structures',['concept:sequences','concept:induction'],'An integer-valued sequence with a recursively defined sum of consecutive differences.', '''
def differences (a : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => differences a n + (a (n + 1) - a n)

theorem result (a : Nat → Int) (n : Nat) : differences a n = a n - a 0 := by
  induction n with
  | zero => simp [differences]
  | succ n ih => simp only [differences, ih]; omega
''')
add('OrderTrans','Bounds propagate through intermediate quantities','Order',['concept:inequalities','reason:bounds'],'Exact integer-order transitivity; no limit passage is involved.', '''
theorem result (a b c d : Int) (ab : a ≤ b) (bc : b ≤ c) (cd : c ≤ d) : a ≤ d := by
  omega
''')
add('OrderAntisymmetry','Two opposite bounds determine equality','Order',['concept:inequalities'],'Integer antisymmetry illustrates why lower and upper bounds can pin down a value.', '''
theorem result (a b : Int) (h₁ : a ≤ b) (h₂ : b ≤ a) : a = b := by
  omega
''')
add('StrictGap','A positive integer gap excludes equality','Order',['concept:inequalities','concept:contradiction'],'An integer gap example, not a real-analysis estimate.', '''
theorem result (a b : Int) (h : a + 1 ≤ b) : a ≠ b := by
  omega
''')
add('SequenceStep','Stepwise monotonicity controls every later term','Sequences',['concept:sequences','concept:induction'],'For an integer-valued sequence, adjacent inequalities imply a bound after any finite number of steps.', '''
theorem result (a : Nat → Int) (h : ∀ n, a n ≤ a (n + 1)) (n k : Nat) :
    a n ≤ a (n + k) := by
  induction k with
  | zero => simp
  | succ k ih =>
    have hs := h (n + k)
    have ht : a n ≤ a ((n + k) + 1) := by omega
    simpa only [Nat.add_assoc] using ht
''')
add('ConstantSequence','Zero consecutive differences force a constant sequence','Sequences',['concept:sequences','concept:dynamics'],'A discrete analogue only; this is not the calculus zero-derivative theorem.', '''
theorem result {α : Type} (a : Nat → α) (h : ∀ n, a (n + 1) = a n) (n : Nat) :
    a n = a 0 := by
  induction n with
  | zero => rfl
  | succ n ih => exact (h n).trans ih
''')
add('Eventually','Two eventual properties hold together eventually','Sequences',['concept:limits','college:limsup'],'A quantified tail argument. It proves no convergence claim by itself.', '''
theorem result (P Q : Nat → Prop)
    (hp : ∃ N, ∀ n, N ≤ n → P n) (hq : ∃ N, ∀ n, N ≤ n → Q n) :
    ∃ N, ∀ n, N ≤ n → P n ∧ Q n := by
  obtain ⟨A, hA⟩ := hp
  obtain ⟨B, hB⟩ := hq
  refine ⟨A + B, ?_⟩
  intro n hn
  exact ⟨hA n (by omega), hB n (by omega)⟩
''')
add('Reachability','Finite graph paths concatenate','Graphs',['concept:graphs'],'A graph is an arbitrary relation; reachability is its inductively defined reflexive-transitive closure.', '''
inductive Reach {α : Type} (edge : α → α → Prop) : α → α → Prop where
  | refl (a) : Reach edge a a
  | step {a b c} : edge a b → Reach edge b c → Reach edge a c

theorem result {α : Type} {edge : α → α → Prop} {a b c : α}
    (ab : Reach edge a b) (bc : Reach edge b c) : Reach edge a c := by
  induction ab with
  | refl => exact bc
  | step e path ih => exact Reach.step e (ih bc)
''')
add('Undirected','Symmetric adjacency reverses a two-edge walk','Graphs',['concept:graphs'],'Only reverses a length-two walk; does not claim a general graph classification.', '''
theorem result {α : Type} (edge : α → α → Prop)
    (symmetric : ∀ a b, edge a b → edge b a) (a b c : α)
    (ab : edge a b) (bc : edge b c) : edge c b ∧ edge b a := by
  exact ⟨symmetric b c bc, symmetric a b ab⟩
''')
add('FiniteValue','An optional value cannot be both absent and present','Finite structures',['reason:deep:finite-valuation'],'A datatype fact underlying the abstract valuation teaching model.', '''
theorem result {α : Type} (x : α) : (none : Option α) ≠ some x := by
  intro h
  cases h
''')
add('VectorDistributivity','Scaling a two-coordinate vector distributes','Algebra models',['concept:vectors','college:bilinear'],'A concrete natural-number pair model. Naturals are not a field, so this is not a general vector-space theorem.', '''
def scale (k : Nat) (v : Nat × Nat) := (k * v.1, k * v.2)
def plus (u v : Nat × Nat) := (u.1 + v.1, u.2 + v.2)

theorem result (k : Nat) (u v : Nat × Nat) :
    scale k (plus u v) = plus (scale k u) (scale k v) := by
  simp [scale, plus, Nat.mul_add]
''')
add('KernelSum','The kernel of an additive map is closed under addition','Algebra models',['concept:linear'],'An exact integer additive-map statement, with additivity supplied as a hypothesis.', '''
theorem result (f : Int → Int) (additive : ∀ a b, f (a + b) = f a + f b)
    (x y : Int) (hx : f x = 0) (hy : f y = 0) : f (x + y) = 0 := by
  rw [additive, hx, hy]
  rfl
''')
(R/'lean-library.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('Generated',len(rows),'additional examples')
