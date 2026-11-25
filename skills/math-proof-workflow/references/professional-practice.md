# How professionals run AI-assisted proving (state as of 25 Nov 2026)

This is a research digest, not gospel. Each claim says how well it is
sourced. Re-check anything you are about to rely on in public.

## Patterns that recur across serious groups

1. **Verifier first, generator second.** Every system that produced real
   results pairs a cheap generator (LLM, search, RL) with a trusted checker
   (Lean kernel, SAT proof checker, exact evaluator). FunSearch (DeepMind,
   Nature 2023, cap sets), AlphaEvolve (DeepMind 2025) and its large study
   with Tao, Georgiev, Gómez-Serrano and Wagner on dozens of problems, and
   Wagner's 2021 RL counterexamples all work this way. The checker is the
   product; the LLM is a mutation operator.
2. **Literature search is the biggest single AI contribution.** Scientific
   American reported in 2026 that most of the ~100 Erdős problems moved to
   "solved" with AI help were moved by souped-up literature search. The
   DeepMind Aletheia paper (arXiv 2601.22401) on the then-700 open problems
   in Bloom's database attributes the open status of those it resolved to
   obscurity rather than difficulty, and several of its results were already
   in the literature. Your guide states 8 of 13; verify the exact count in
   the paper before quoting it.
3. **Tao's calibration.** Tao has said Erdős problems vary in difficulty by
   orders of magnitude, that only a small percentage of open ones are within
   reach of current tools with little human help, and that unreported
   failures make success rates look better than they are. (Secondary
   coverage: The Decoder, TechCrunch, Jan 2026.) Practical reading: pick from
   the long tail, and publish your failures too.
4. **Formalise, then rewrite for humans.** The reported Erdős #728 workflow
   (Jan 2026): model drafts the argument, Aristotle formalises it in Lean and
   repairs small gaps, then a model turns the formal proof back into readable
   prose. Lean is the trust anchor; the prose is the deliverable for people.
5. **Red team / blue team.** Use one model to generate and a different
   instance, ideally a different model, to attack. Same-model self-review
   shares blind spots.
6. **SAT with certificates for finite statements.** Boolean Pythagorean
   triples (Heule et al. 2016), Schur number five (Heule 2017), Keller's
   conjecture in dimension 7 (2020), and the empty hexagon theorem (Heule and
   Scheucher 2024, with the encoding itself verified in Lean) are the
   template: encode, solve, emit a DRAT/LRAT proof, check it with a verified
   checker, and verify the encoding.

## Infrastructure you will meet

| Thing | What it is | Status |
|---|---|---|
| formal-conjectures (google-deepmind) | Lean statements of open problems, `@[category research open]` tags | Pins `leanprover/lean4:v4.33.1`, monthly Mathlib (read 25 Nov 2026) |
| Palomar registry | Registry of Lean-checked results; checks proof against statement with Comparator, plus a model-assisted check of statement vs informal description | Launched 18 Aug 2026. formal-conjectures requires a Palomar link for `@[formal_proof]` on solved problems |
| erdosproblems.com | Thomas Bloom's database and forum | A news headline says comments were closed due to a flood of AI proofs; not confirmed. Read the forum rules the day you post |
| teorth/erdosproblems wiki "AI contributions to Erdős problems" | Tracker of AI attempts: green full, yellow partial, red incorrect, white unverified | Page says it stopped updating; data as of 30 Jun 2026. Look for its successor before relying on it |
| FrontierMath: Erdős (Epoch AI) | 68 problems open as of Aug 2026, chosen by Bloom; Lean proofs required; $300 and 72 h per attempt | Launched 1 Sep 2026; Epoch reported 17 of the 68 solved by anyone by late Oct 2026. Those problems are a race against labs |
| Aristotle (Harmonic) | Automated prover service | **aristotlelib ≥ 3 dropped Lean.** Its README (v3.4.0, 18 Nov 2026) says it verifies Verilog, C and Rust and "doesn't verify pure mathematics or Lean". See `auto-prover` |
| lean-lsp-mcp | MCP server giving goals, diagnostics, LeanSearch, Loogle, Lean Finder, hammer premises | External search tools are rate-limited to 3 requests / 30 s each on hosted services |
| Open-weight provers | DeepSeek-Prover-V2, Goedel-Prover(-V2), Kimina-Prover | Good on competition-level leaves; weak on research-level goals |

## Weakly sourced, treat with care

- "AlphaProof Nexus resolved 9 of 353 open Erdős problems" (May 2026, said to
  be in Science, Oct 2026): seen only in secondary sources and an arXiv
  listing; it reportedly also found misformalisations.
- Specific FrontierMath Erdős leaderboard numbers: sources disagree; read the
  live page.

## Sources

- Epoch AI, FrontierMath Erdős: https://epoch.ai/benchmarks/frontiermath-erdos
- Aletheia / Erdős study: https://arxiv.org/abs/2601.22401
- Scientific American coverage: https://www.scientificamerican.com/article/ai-uncovers-solutions-to-erdos-problems-moving-closer-to-transforming-math/
- Tao on GPT-5.2 Pro and #728: https://the-decoder.com/terence-tao-says-gpt-5-2-pro-cracked-an-erdos-problem-but-warns-the-win-says-more-about-speed-than-difficulty/
- Quanta, Aug 2026: https://www.quantamagazine.org/how-ai-tore-through-a-mathematical-community-20260803/
- AI contributions wiki: https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems
- Palomar coverage: https://runtimewire.com/article/palomar-lean-proof-registry-ai-mathematics
- formal-conjectures: https://github.com/google-deepmind/formal-conjectures
- lean-lsp-mcp: https://github.com/oOo0oOo/lean-lsp-mcp
- Aristotle: https://github.com/harmonic-ai/aristotle
