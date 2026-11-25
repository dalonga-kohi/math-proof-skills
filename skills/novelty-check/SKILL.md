---
name: novelty-check
description: Same-day check that a verified result is genuinely new - re-reads the problem's tracker page and forum thread, searches arXiv, Google Scholar, zbMATH, MathOverflow and OEIS, checks AI-attempt trackers, formal-conjectures pull requests and the Palomar registry, and writes a search log. Use after verify-gate passes and before announcing any result, when the user asks "is this known?", "has this been solved?", or when an LLM claims a new theorem.
license: Apache-2.0
compatibility: Needs web search/fetch tools or a human to run the searches. Some sites (erdosproblems.com, arxiv.org) may need to be allowed in a sandboxed network.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Novelty check

Prior: the result is probably already known. In DeepMind's 2026 study of the
then-700 "open" Erdős problems, much of what the AI resolved turned out to be
in the literature already (your guide cites 8 of 13), and the paper attributes
the open status to obscurity rather than difficulty. A literature hit is the
most likely outcome, and finding it is useful: it lets the tracker be updated.

## Protocol (do all of it, the same day you announce)

Write each search with its query and result into `Work/<Id>/NOVELTY.md`.

1. **Source page, today.** Re-read the problem's page (erdosproblems.com/N,
   OEIS entry, MathOverflow question) and its comments/forum thread. Status
   changes daily on active problems.
2. **Problem identifiers.** Search "Erdős problem N", "Erdős #N", the
   problem's common name, and the OEIS A-number if any, on arXiv (full text
   via Google Scholar), Google Scholar, zbMATH Open, MathSciNet if available.
3. **Mathematical content.** Search the statement's key phrases and the
   *result* phrased several ways ("every Sidon set in [N] has", "maximal
   B_2 sequence"), plus synonyms the field uses (Sidon = B₂ = Golomb ruler).
   Old results hide under old names.
4. **Citation chase.** Open the original source (the Erdős paper) on Google
   Scholar, "Cited by", and scan titles and abstracts. Check recent surveys.
5. **AI-attempt records.** The teorth/erdosproblems wiki "AI contributions
   to Erdős problems" (stopped updating; data as of 30 Jun 2026 — look for a
   successor), Epoch AI's FrontierMath: Erdős page, lab announcements.
6. **Formal records.** formal-conjectures: open and recently closed PRs and
   issues mentioning the problem; the file's git log. Palomar registry
   search. Mathlib and Zulip (#Formal conjectures, #Machine Learning for
   Theorem Proving) for the problem number.
7. **Ask a model to play literature scout** with the statement and result
   (agents in `math-swarm` include one), but treat every citation it gives
   as a lead to verify, never as evidence: models invent references.

## Verdict

```
verdict: new | known (cite) | partially known (cite; what is new) | inconclusive
searched: <list of sources + dates>
closest prior work: <citations, with what they prove>
```

If known: you still have something useful. Update the tracker / forum with
the reference ("this follows from Theorem 3 of X (1987)"), and, if Lean-checked,
offer the formal proof to formal-conjectures as a solved variant.

If inconclusive: say so in the write-up ("we could not find this in the
literature; searches: …"). Never claim novelty you did not check.
