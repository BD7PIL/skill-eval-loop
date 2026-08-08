# skill-eval-loop

Meta-skill: closed-loop validation & optimization of Agent Skills.

Guides the orchestrating agent through dry-run round-based closure for
complex-domain skills (DSL/code/test-program generation, real compiler/runtime
validation):

```
Prepare → Test → Attribute → Fix → Regress
```

- **Test**: fresh-agent isolated rerun (no golden, no context), EXECUTION_LOG
- **Attribute**: three-way (doc defect / execution error / environment) by the
  orchestrator, never by the executing subagent
- **Fix**: docs/scripts only — never hand-edit dry-run artifacts (fake closure)
- **Regress**: every defect frozen as a deterministic assertion

## Grader pyramid

| Tier | Check | Speed |
|---|---|---|
| L1 | static asserts | sec |
| L2 | syntax (SSF/LSP) | sec-min |
| L3 | real build, 0 errors | min |
| L4 | run + results (only pass definition) | min |

## Layout

```
skills/skill-eval-loop/
├── SKILL.md
├── references/
│   ├── protocol_template.md      # generic dry-run protocol
│   ├── attribution.md            # three-way attribution + traps
│   ├── assertions.md             # defect→assertion pattern library
│   └── case_study_wlg5144.md     # first application (R1-R6)
└── scripts/
    ├── run_evals.py              # grader-pyramid executor (parameterized)
    └── init-protocol.py           # protocol skeleton generator
```

Complements [skill-creator](https://github.com/anthropics/skills) (authoring);
generic eval tools (skill-up, skillgrade) are optional execution-layer helpers,
not required — the core loop uses the host's task system + domain verifiers.

## Install

```bash
# symlink into a project's skill dir (no hard copy):
ln -s ../../../../tools/skill-eval-loop/skills/skill-eval-loop <project>/.agents/skills/
```

## Quick start

```bash
python3 skills/skill-eval-loop/scripts/init-protocol.py my-skill /tmp/out
python3 skills/skill-eval-loop/scripts/run_evals.py <project_root> <prog_rel> \
    [--device NAME] [--assert-file asserts.json] [--skip L1 L2 L3 L4]
```
