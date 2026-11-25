Construct a Sidon set A ⊆ {1, …, 1000}: all sums a + b with a ≤ b, a, b ∈ A, are
distinct. `construct()` returns a list of integers. Score = |A| (invalid sets are
rejected by the evaluator). Context: the maximum is sqrt(N) + O(N^{1/4})
(Erdős–Turán; Lindström's bound gives at most about N^{1/2} + N^{1/4} + 1 ≈ 38
here). Singer difference sets (prime power q, q+1 elements mod q²+q+1) and
their translates/dilates restricted to an interval are the classical
constructions; greedy (the seed) gets 27.
