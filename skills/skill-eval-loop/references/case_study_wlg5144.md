# Case Study: WLG5144 v93k-smartest8-dev (R1-R6)

First full application of the eval loop on a complex-domain skill (ATE test
program generation: DSL files needing real Eclipse compile + offline run).
Raw materials: `WLG5144_dev/docs/dryrun2_protocol.md`,
`research-skill-test-loop-2026-08-08.md`, project memory.

## Timeline (compressed)

| Round | What happened | Attribution |
|---|---|---|
| R1 | Baseline: fresh agents ran full pipeline; behavior passed but 2 defects found (ODS from-scratch path missing; scaffold unfriendly error) | Doc defects |
| R2 | Added `--create-template-from-scratch` + doc structure table; scaffold message | Fixes |
| R3 | Fresh agent rerun exposed 3 NEW defects: spec units (bare doubles fail compile), ODS headers wrong (reader-verified ≠ writer export), flow limits misleading | Doc defects — earlier fixes were incomplete because verification stopped at L2 (syntax) |
| R4 | **FAKE CLOSURE**: orchestrator hand-added flow limits + hand-patched ODS to make run pass | Methodology violation (fake closure) |
| R5 | Zero-touch round: fresh agent produced full pipeline; flow limits ACTIVE per doc; run_evals PASSED | Real closure #1 |
| R6 | Architecture change: flow limits ABSENT (ODS single source of truth); seed via --override; run_evals L1 added flow-no-limit assert; zero-touch rerun PASSED | Real closure #2 |

## Key lessons

1. **L2 pass ≠ L3 pass**: R3's three defects were all invisible to SSF syntax
   checks. Only Eclipse compile (L3) and run (L4) caught them. Never gate on
   low-fidelity alone.
2. **Fake closure is easy and silent**: R4 "passed" because the orchestrator
   backfilled limits. The tell: artifacts changed outside the fresh-agent
   session. Antidote: after any fix, a zero-touch round must reproduce.
3. **Flow limits mislead ATE engineers** → ODS-only architecture. Rule:
   generated flow must NOT carry parametricTestDescriptor (ODS is the single
   source of truth; seeds injected at ODS generation via --override).
4. **Golden is not the only answer**: dry-run physical values (vrange/irange/
   iclamp) differed from golden yet were bind-legal and passed. Byte-diff would
   have mis-attributed legal alternatives.
5. **Doc-vs-doc conflicts surface late**: SKILL.md said "chip max vClamp" while
   two reference docs said "per-IO-domain". Agent chose the physically-correct
   option. Fix: make SKILL.md point to the reference (single source).
6. **Stale doc cache**: agent loaded a cached old SKILL.md. Trust disk; confirm
   version executed.
7. **Kill via official wrapper**: `prod_env/lbin/kill_smarTest -f` (passes
   version-matched kill patterns); bare `kill_SmarTest` misses the eclipse
   watcher which respawns Eclipse → cleanup looks done, isn't.

## Cost of this validation approach

- ~6 rounds × (10-15 min fresh agent + 5-10 min orchestration) ≈ 2-3 hours total
- Each round is fully reproducible from git: skill version + protocol + verifier
  commands.

## Reusable assets produced

- `run_evals.py` (now parameterized in skill-eval-loop)
- ODS generation patterns (from-scratch template + populate + override)
- Assertion patterns: units-in-spec, flow-no-limits, ODS headers/±MAX,
  src/src double path, TODO residue
