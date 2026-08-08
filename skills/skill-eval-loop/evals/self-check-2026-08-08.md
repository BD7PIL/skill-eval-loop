# Self-check record (2026-08-08)

The meta-skill validated itself on real artifacts (R6 dryrun2 output of
v93k-smartest8-dev) + injected regressions.

## 1. Real artifact (R6 dryrun2) — L1 must PASS

Command (device auto-derived from .project_config.json):
```
python3 scripts/run_evals.py <dryrun2>/WLG5144 <prog> --skip L2 L3 L4
```
Result: 8/8 PASS (no src/src, no TODO_LLM, spec units, flows no limits,
ODS 7 sheets, Software_Bins 6 cols, 20 data rows, no +/-MAX).

## 2. Injected regressions — asserts must FAIL (RED)

| Injection | Assertion | Result |
|---|---|---|
| flow gains active parametricTestDescriptor | P5 flows-no-limits | FAIL @ Continuity.flow:28,29 ✓ |
| spec gains bare `level.vrange = 2;` | P4 units | FAIL @ line 19 ✓ |
| src/src dir created | P1 no double path | FAIL ✓ |

## 3. Self-found defects fixed

- `run_evals.py` printed `±MAX` (non-ASCII) → UnicodeEncodeError on Python 3.6
  ASCII stdout. Fixed to `+/-MAX`. (Caught by running the tool on itself —
  the methodology works.)

## 4. Notes

- Injection must match the artifact's actual format (R6 uses `2V` not `2.0V`;
  a `2.0V`-targeted injection silently no-op'd — assert validity depends on
  testing the assert itself with a REAL mutation).
