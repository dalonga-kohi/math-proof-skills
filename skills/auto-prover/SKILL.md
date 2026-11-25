---
name: auto-prover
description: Dispatches routine leaf lemmas (the remaining sorries) to automated provers - Lean's own automation and hammer premises, open-weight provers such as DeepSeek-Prover-V2, Goedel-Prover-V2 and Kimina-Prover served locally, and hosted services such as Harmonic's Aristotle where they still accept Lean - with Lean as the only judge. Use when a Lean file has several small sorries left, when a goal is routine but tedious, or when the user mentions Aristotle, DeepSeek-Prover, Goedel-Prover, Kimina or "auto-prove the sorries".
license: Apache-2.0
compatibility: Needs lake and Python 3.10+. Local provers need a GPU and an OpenAI-compatible server (vLLM/SGLang). Hosted provers need network access and an API key.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Auto-prover for leaf lemmas

Division of labour: a strong general model (you) owns the idea and the
lemma structure; automated provers grind leaves. Do not send the main
theorem of an open problem to a leaf prover and hope.

## 1. Find the leaves

```bash
python3 scripts/extract_sorries.py Work/Erdos123/Main.lean
python3 scripts/extract_sorries.py Work/Erdos123/Main.lean --split Work/Erdos123/leaves
```

Each split file ends with one target declaration and keeps every earlier
lemma available as a black box.

## 2. Escalation ladder (cheapest first)

1. **Built-in automation** via `lean_multi_attempt` at the sorry:
   `["simp", "omega", "decide", "norm_num", "linarith", "nlinarith", "positivity", "aesop", "exact?"]`
   (add `grind` if the pinned toolchain has it). Seconds, free.
2. **Premise hints**: `lean_hammer_premise` at the goal, then retry
   `simp [p1, p2]` / `aesop (add safe p1)`.
3. **Open-weight prover, pass@k** (`scripts/local_prover.py`). Serve a prover
   with vLLM and run k samples; Lean filters them.
   ```bash
   vllm serve deepseek-ai/DeepSeek-Prover-V2-7B --port 8000
   python3 scripts/local_prover.py Work/Erdos123/leaves/00042_l3.lean --project . \
       --model deepseek-ai/DeepSeek-Prover-V2-7B --template deepseek -k 32
   ```
   These models are strong on competition-style goals and weak on
   research-level ones. They were trained on older Mathlib, so expect renamed
   lemmas; the compile loop handles it. The script rejects any candidate that
   changes the statement or uses `sorry`/`axiom`/`native_decide`.
4. **Hosted provers** (see the Aristotle note below).
5. **Back to you**: if a leaf resists all of the above, it is probably not a
   leaf. Re-split it (`proof-blueprint`, lemma-splitting prompt) or check it
   is true.

Splice accepted proofs back into the main file by hand (or have the agent do
it), recompile, and run `verify-gate`. A prover's own success message is not
verification.

## Aristotle (Harmonic): status as of 25 Nov 2026

Your guide's command, `uvx --from aristotlelib aristotle prove-from-file file.lean`
with `ARISTOTLE_API_KEY`, was the pre-3.0 interface. The current package
(aristotlelib 3.4.0, released 18 Nov 2026) says in its README that Aristotle
verifies Verilog, C and Rust and "doesn't verify pure mathematics or Lean"; its
changelog says 3.0 removed `aristotle formalize`, and 3.2 stopped treating
Lean as code to verify (the CLI exits 2 when only `.lean` files would be
uploaded).

What that means for you:

- `uvx --from aristotlelib …` now resolves to 3.x and will not prove Lean.
- Pinning the old client, `uvx --from "aristotlelib<3" aristotle prove-from-file file.lean`,
  may or may not still work: it depends on whether Harmonic's servers still
  serve the old endpoint. That was not verified. Try it once on a trivial
  file; if it fails, drop Aristotle from the ladder.
- Harmonic also lists a hosted MCP server
  (`claude mcp add --transport http --scope user aristotle https://aristotle.harmonic.fun/mcp`);
  check its tool list for Lean support before relying on it.
- Uploading an unpublished result to any third-party service shares it with
  that service. On race problems (FrontierMath: Erdős list), decide that
  deliberately.

## Budgeting

- Parallelise pass@k across leaves, not across samples of one hard leaf.
- Stop a leaf after k = 64 local samples or 2 hosted attempts; that is a
  signal to re-split.
- Log every attempt (prover, k, outcome) in `NOTES.md`; failure statistics
  tell you which lemmas are actually hard.
