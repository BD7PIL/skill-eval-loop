# Attribution Methodology

How the orchestrator attributes a round's failures, and the traps that corrupt it.

## 1. Three-way attribution

| Class | Evidence | Action |
|---|---|---|
| **Doc defect** | Rule wrong/vague/missing in skill docs; subagent followed doc and produced wrong output | Fix the doc + add regression assertion |
| **Execution error** | Subagent deviated from doc (assumption not recorded, skipped step) | Rerun or emphasize the rule in doc |
| **Environment issue** | Tool bug, verifier quirk, stale state, daemon respawn | Record gotcha (project memory), do NOT change doc |

Attribute to the SMALLEST unit first: which flow → subflow → parameter → doc line.

## 2. Verification before attribution (critical)

**Never attribute before confirming with the highest-fidelity verifier available
at that layer.**

- L1 pass ≠ L2 pass (grep-clean file may not parse)
- L2 pass ≠ L3 pass (syntax-clean DSL may fail compile: wrong types, missing refs)
- L3 pass ≠ L4 pass (compiles but run fails: bind errors, ODS mismatch, unset limits)

Classic failure: "SSF/syntax clean" reported as success, then compile/run exposes
errors the syntax check never saw. If you attributed a doc defect based on a
low-fidelity pass, the fix is wrong.

## 3. Subagent self-report is not evidence

Subagents claim completion; verify independently:
- diff generated artifacts vs golden
- run the verifier yourself
- read EXECUTION_LOG for verbatim obstacles (do not trust summaries)

## 4. LLM self-attribution is biased

A subagent that both executes AND attributes will:
- mis-attribute its own execution errors to doc defects (self-preservation bias)
- propose fixes aligned with its own misunderstanding

Hence: subagent records phenomena only; orchestrator attributes. (R1 of the
WLG5144 case: 23 candidate defects from self-attributing agents → after
orchestrator verification only 8 were real; 2 were false positives.)

## 5. Fake closure (the cardinal sin)

Hand-editing dry-run artifacts to make them pass = fake closure. The validation
"skill doc works" becomes "orchestrator worked". Symptoms:
- artifacts edited outside the fresh-agent session
- limits/values backfilled by the orchestrator after the fact
- "run passed" attributed to a doc rule the agent never wrote

Antidote: after any fix, a NEW round must reproduce with zero orchestrator
artifact edits. The WLG5144 R4 closure was fake for exactly this reason; R6
(zero-touch) was the first real pass.

## 6. Golden is not the only correct answer

Byte-diff against golden mis-attributes legal alternatives:
- physical values (vrange/irange/iclamp) may differ from golden yet be
  bind-legal — golden is one legal point, not the unique answer
- naming/comments differ legitimately

Use semantic asserts: structure/naming rules = deterministic; physical values =
"legal range + run passes", NOT equality.

## 7. Clean-slate discipline

- Kill services with official wrapper scripts (bare `kill -9` misses respawning
  daemons: eclipse_watcher restarts Eclipse → cleanup appears done, isn't)
- Delete dry-run dir AND workspace together
- Verify: 0 processes + ports released before starting a round

## 8. Doc-cache trap

Agents may load a cached old SKILL.md (observed: agent saw "Flow limits
commented" while disk said "Flow limits ABSENT"). Trust the disk; state the
version you executed; if a conflict appears, re-read the file.

## 9. When to escalate

- Same defect appears in 2 consecutive rounds → the fix was superficial; dig to
  the root rule (often a template the agent copies from, not the prose rule)
- A "fixed" rule regresses in a later round → the assertion was missing; add it
- 3 failed attempts on one defect → stop, document attempts, consult user/oracle
