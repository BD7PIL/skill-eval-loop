---
name: skill-eval-loop
description: >-
  Meta-skill for closed-loop validation and optimization of EXISTING Agent Skills
  (complex domains: DSL/code/test-program generation, real compiler/runtime
  dependencies). USE THIS whenever ANY of these appear:

  - User is developing, debugging, or validating an Agent Skill (not the
    business task the skill produces — the skill itself)
  - "the skill's documented rules disagree with real tool behavior", "the skill
    keeps failing after reruns", "every round exposes new defects", "unsure
    whether an edit actually improved the skill"
  - Reviewing/improving a skill's docs, references, or prompts; planning a
    dry-run validation of a skill; setting up regression/evals for a skill
  - A skill fails in ways that look like doc defects (rules wrong/vague/missing)
    rather than execution errors
  - User mentions: "skill 开发", "skill 调试", "skill 验证", "dry run",
    "fresh agent 重跑", "回归断言", "grader", "方法学"

  Do NOT use for: the business task the skill performs (e.g. generating a test
  program — that is the business skill's job, e.g. v93k-smartest8-dev);
  from-scratch skill authoring (that is skill-creator).

  What it does: guides the agent through dry-run round-based closure —
  fresh-agent isolated rerun → orchestrator attribution (three-way: doc defect /
  execution error / environment) → skill fix → defect frozen as regression
  assertion → tiered validation (L1 static → L2 syntax → L3 build → L4 run =
  the ONLY pass definition) — until the skill doc independently produces a
  runnable result from a fresh agent. Complements skill-creator (authoring).
  Methodology guide only: domain verifiers (compilers, LSP, Eclipse bridge) are
  injected by the consuming project.
---

# Skill Eval Loop — Meta-skill for Closed-Loop Skill Validation & Optimization

## Positioning (read first)

- **Consumer**: the orchestrating agent developing/optimizing an Agent Skill.
  NOT a runtime dependency of the business skill itself.
- **Output**: dry-run protocol, static assertions, regression suite, round records —
  i.e. supporting dev documents + verification scripts.
- **Division with skill-creator**: skill-creator authors a skill from scratch
  (capture intent → draft → test → evaluate → improve); this skill validates and
  optimizes an EXISTING skill (complex domains where from-scratch authoring cannot
  be done by a few interactions).
- **Division with tooling**: this is the knowledge layer (how to organize the loop);
  the execution layer uses the domain's real verifiers (compiler/LSP/runtime/
  custom scripts). Generic eval tools (skill-up, skillgrade) are optional — the
  core loop does NOT depend on them: fresh-agent isolated rerun requires the host's
  task system, which generic tools typically do not cover.

## Core Loop Protocol (one round per defect)

```
Prepare → Test → Attribute → Fix → Regress → (converge or next round)
```

### Phase 0 — Prepare (start of each round)

1. **Clean slate**: kill all related services (use official wrapper scripts, never
   bare kill of process trees — see Gotchas), delete the dry-run directory and its
   workspace (stale artifacts pollute).
2. **Document consistency check**: skill docs edited this round must match script
   behavior (param names, rule wording). The agent executes BY the docs — vague
   docs = expected defect.
3. **Baseline snapshot**: record skill version (git hash), verifier versions,
   environment state.

### Phase 1 — Test (fresh-agent isolated execution)

- Use a **fresh subagent** (no context, forbidden to read golden/reference
  artifacts) executing the target task per the skill doc.
- **Isolation**: separate directory; no reading golden projects (leakage corrupts
  attribution — SkillsBench-verified).
- **EXECUTION_LOG.md**: the subagent records every command, verbatim obstacles,
  assumptions. Fixed sections (Steps / Obstacles / Assumptions / Status).
- **Subagent must NOT attribute**: it records phenomena only (verbatim error
  text), never "the doc should say X". Attribution is the orchestrator's job
  (LLM self-attribution is biased — see attribution.md).

### Phase 2 — Attribute (orchestrator)

1. **Verify artifact authenticity**: never trust the subagent's self-report —
   independently check with diff/grep/run output.
2. **Three-way attribution** (see references/attribution.md):
   - **Doc defect** (rule wrong/vague/missing) → fix the doc
   - **Execution error** (agent deviated from doc) → rerun or emphasize in doc
   - **Environment issue** (tool bug/env state) → record gotcha, do NOT change doc
3. **Key trap**: low-fidelity pass ≠ real pass (e.g. "syntax check passed" ≠
   "compiles"). Always confirm with the highest-fidelity verifier available at
   that layer before attributing.

### Phase 3 — Fix (minimal fix)

- **Only edit skill docs/scripts. NEVER hand-edit dry-run artifacts.** Hand-editing
  artifacts = fake closure (artifacts must be 100% fresh-agent output per the doc,
  otherwise validation is void — the single most important discipline of this
  methodology).
- Each fix lands in two places: the rule AND the anti-regression assertion
  (Phase 4).

### Phase 4 — Regress (defect → permanent regression assertion)

Every fixed defect becomes a **deterministic assertion**, never regressable:

- Static assertions (grep/schema) → into the L1 assertion set
- Compile/run assertions → into L3/L4
- Assertions live in the protocol's verification script; failure exits non-zero

## Grader Pyramid (tiered acceptance gates)

| Tier | Check | Speed | Failure semantics |
|---|---|---|---|
| L1 | Static asserts: structure/naming/units/no-hardcode/known anti-patterns | sec | structural regression |
| L2 | Syntax/type check (language server, compiler frontend) | sec-min | syntax regression |
| L3 | Real build/compile (0 errors) | min | compile regression |
| L4 | Run + result verification (**the ONLY pass definition**) | min | behavioral regression |

**Tier selection rules**:
- Prefer deterministic verifiers (grep/compiler/runtime asserts) over LLM graders
  (costly and unreliable).
- Acceptance gate = L4 (run). L1-L3 are fast-fail pre-gates, never substitutes.
- Every tier failure needs a **concrete assertion** (not "eyeball check") — one
  failure = one new assertion.

## Round Management

- One round = one full Prepare→Regress. The only variable between rounds = skill
  edits (clean attribution).
- **Convergence criteria** (ALL must hold):
  1. Whitelisted-external diff = 0 (golden comparison uses SEMANTIC asserts, not
     byte equality — golden is not the only correct answer; physical values pass
     on "legal range / run passes")
  2. L1-L4 all green (run_evals one command)
  3. Fresh agent completes the full workflow with ZERO human artifact edits
  4. User confirmation
- **Whitelist** (not defects): naming diffs, comments/formatting, build artifacts
  (dsa_gen/bin/.abin etc.), timestamps, legal alternative physical values
  (bind-legal suffices).

## Assertion Pattern Library (references/assertions.md)

Defect → assertion extraction patterns:
- "artifact must not contain X" → grep assert (hardcode, TODO residue)
- "structure must be correct" → schema/header assert
- "naming must be consistent" → cross-file reference consistency assert
- "value must be legal" → range/bind-legal assert (NOT equality to golden)
- "no anti-patterns" → anti-pattern grep (duplicate props, double paths)

## Bundled Scripts

- `scripts/run_evals.py` — grader-pyramid executor (configurable L1 static asserts
  + L2-L4 calling domain verifiers). Domain verifiers injected via params
  (bridge/compile/run commands).
- `scripts/init-protocol.py` — generates a dry-run protocol skeleton +
  EXECUTION_LOG template for a new skill.

## Gotchas (battle-tested)

- **Hand-editing artifacts = fake closure**: validation must be based on the fresh
  agent's raw output.
- **Kill services with official wrapper scripts**: bare process-tree kill misses
  daemons that auto-respawn (e.g. eclipse watcher) → cleanup looks successful but
  isn't.
- **Low-fidelity verifier masquerading as acceptance gate**: syntax-pass ≠
  compile-pass ≠ run-correct. Escalate to L4.
- **Subagent self-report is not evidence**: orchestrator must independently verify
  artifacts (diff/run).
- **Stale doc cache**: agents may load a cached old SKILL.md — trust the disk,
  confirm before executing.
- **Isolation leakage**: a fresh agent that read golden pollutes attribution —
  forbidden.

## Reference Files

- `references/protocol_template.md` — generic dry-run protocol template (round
  table / EXECUTION_LOG / convergence / whitelist, parameterized)
- `references/attribution.md` — attribution methodology (three-way + low-fidelity
  traps + cases)
- `references/assertions.md` — assertion pattern library (defect → assert)
- `references/case_study_wlg5144.md` — first application case (R1-R6, incl. the
  fake-closure lesson)

## Implementation Scope

- Phase 1 protocol + Phase 2 attribution + Phase 3 assertion patterns: ✅ included
- Domain-verifier integration: provided by the consuming project (injected params)
- Generic eval tool integration (skill-up/skillgrade): optional, not bundled
