# Dry-Run Protocol Template (generic)

Parameterized template for validating an Agent Skill via fresh-agent rounds.
Replace `<SKILL>`, `<PROJECT_DIR>`, `<GOLDEN_DIR>`, `<VERIFIER_CMD>` per project.
Derived from the WLG5144 v93k-smartest8-dev case (see case_study_wlg5144.md).

## 1. Goal

Validate that `<SKILL>`'s documentation independently produces a runnable result:
fresh subagents (no context) execute the skill end-to-end; the orchestrator checks
artifact quality, attributes defects, fixes the skill, and freezes defects as
regression assertions. Rounds iterate until convergence.

**"Converge" means**: the skill's METHOD chain (not memorized golden values)
reliably produces legal outputs — e.g. physical values must derive from
spec→verifier-error legal ranges, not hardcoded numbers.

## 2. Division of roles

| Role | Responsibility |
|---|---|
| Subagent (fresh, no context) | Execute the task + record phenomena (EXECUTION_LOG.md). **Forbidden**: analyzing skill defects ("the doc should say X"), reading golden/reference dirs |
| Orchestrator (main agent) | Verify artifact quality (diff vs golden / EXECUTION_LOG review / run results), attribute (doc defect vs execution error vs environment), fix skill, drive rounds |
| User | Review fix direction, confirm convergence |

## 3. Round structure

```
Round N = clean slate → sequential subtasks (each a fresh subagent)
       → orchestrator check/attribute → skill fix → Round N+1 (full rerun)
```

Only variable between rounds = skill edits → clean convergence curve.

## 4. Subtask sequence (fixed per round)

| # | Subtask | Deliverable | Verify |
|---|---|---|---|
| T1 | Phase 1 scaffold | skeleton + config | diff vs golden + L1 |
| T2 | Phase 2 hardware config | generated files | diff + L1 |
| T3..N | Domain/task subtasks | per-skill deliverables | diff + L2/L3 |
| T(N+1) | Run & iterate | build 0 errors + run + results | L4 (only pass definition) |

Order dependency: T(n) consumes T(n-1) artifacts via the filesystem (prompt gives
paths, not content).

## 5. Subagent prompt (six sections)

```
TASK            the single goal
EXPECTED OUTCOME deliverables + expected verification output
REQUIRED TOOLS  bash/python/skill scripts/verifier commands
MUST DO         follow SKILL.md section; write EXECUTION_LOG.md; record obstacles
                verbatim; record assumptions; never stall
MUST NOT DO     no reading golden/reference; no skill-doc analysis; no skill-file
                edits; no out-of-scope generation
CONTEXT         paths / testplan location / prior-subtask outputs / Python version
                / verifier state
```

## 6. EXECUTION_LOG.md format (subagent must write, at project root)

```markdown
## Task: <T# name>
## Steps (commands + output summaries, in order)
## Obstacles (verbatim error text, one per entry)
## Assumptions (choices when doc was vague + rationale)
## Status (complete/partial/stuck)
```

## 7. Orchestrator check flow (after each subtask)

1. Artifact diff vs golden (whitelist rules §8)
2. EXECUTION_LOG review → attribute each obstacle
3. (optional) session-log spot check at key decision points
4. Verifier run (L1-L4 tiers)
5. Write attribution into round table §10

## 8. Whitelist diffs (not defects)

- Naming diffs (golden manually renamed)
- Comments/formatting/whitespace
- Build artifacts: `dsa_gen/` `bin/` `.abin/` `.src-gen/` `.src-gen-flow/`
- Timestamps, .settings entry order
- **Everything else = defect candidate** (record + attribute)

## 9. Convergence criteria (ALL)

1. Whitelist-external diff = 0 (held for one full round)
2. Behavioral verification: build 0 errors + run passes + legal results
   (non-zero/legal values, real limits — not ±MAX placeholders)
3. Physical values reproduced via the method chain (no hardcoded source)
4. User confirmation

## 10. Round record table

| Round | Skill fixes | External diff count | L1-L4 | Conclusion |
|---|---|---|---|---|
| R1 | — (baseline) | | | |
