# Assertion Pattern Library

Defect → deterministic assertion extraction patterns. Every pattern is a template;
concrete asserts are injected per project (in `run_evals.py` L1 config or the
project's verifier).

## P1. "Artifact must not contain X"

Defect class: forbidden residue (hardcoded values, TODO markers, stale paths,
double-paths, non-ASCII in DSL).

```python
# anti-pattern: hardcoded device values in skill output
bad = grep(r'vrange = [0-9.]+V', spec)  # must come from variable expression
# anti-pattern: TODO_LLM residue
bad = grep(r'TODO_LLM', generated_dir)
# anti-pattern: src/src double path
assert not os.path.isdir(project + '/src/src')
```

## P2. "Structure must be correct"

Defect class: wrong schema/headers/columns (e.g. ODS reader rejected
`Mandatory columns missing`).

```python
# header assertion (order matters for some sheets)
cells = read_headers(ods, 'Software_Bins')
assert cells[:6] == ['Software Bin Name','Software Bin','Hardware Bin',
                     'Result','Color','Priority']
# sheet presence
assert {'Tests','Profile',...} <= set(sheets)
```

## P3. "Naming must be consistent"

Defect class: cross-file reference drift (group id in flow ≠ SignalGroups.spec;
ODS row key ≠ flow id; ORE action name ≠ group id).

```python
flow_ids = set(re.findall(r'(?:signalGroup|dpsSignalGroup)\[(\w+)\]', flow))
spec_ids = extract_group_names(signalgroups_spec)
assert flow_ids <= spec_ids          # G4 rename-sync
# ODS row keys match flow ids
ods_keys = extract_ods_row_keys(ods)
assert flow_ids == {k.split('[')[1].rstrip(']') for k in ods_keys}
```

## P4. "Value must be legal"

Defect class: out-of-range/placeholder values (±MAX, 0.0 without ORE, bare
numbers where typed quantities need units).

```python
# spec level props MUST carry units (typed quantities)
bad = [l for l in spec if re.match(r'level\.(vrange|irange) = [0-9.]+;', l)]
assert not bad            # "2.0" fails compile: Cannot assign 'Double' to 'Voltage [V]'
# limits must not be ±MAX (unset placeholder)
for row in ods_test_rows:
    assert row.low != '1.7976931348623157E308'
# physical values legal = bind-legal (not golden-equality)
# (verified implicitly by L4 run passing without bind errors)
```

## P5. "No anti-patterns in generated code"

Defect class: duplicate properties (LLM "fix" added a line without deleting the
original), commented-out active code that misleads, wrong parameter container.

```python
# duplicate property in one block
for block in flow_blocks:
    assert len(re.findall(r'^\s*iRange\s*=', block, re.M)) <= 1
# flow must NOT carry active limits (ODS is single source of truth)
active = [l for l in flow if 'parametricTestDescriptor' in l
          and not l.strip().startswith('//')]
assert not active
```

## P6. "Forbidden feature/pattern absent"

Defect class: known-broken constructs that compile but fail at run
(dpsSignals on mixed-card OpenShort, gAllDPS single block, import in .flow).

```python
# .flow files must NOT have import statements
assert 'import ' not in flow_content
# OpenShort suite must not carry dpsSignals
for suite in openshort_suites:
    assert 'dpsSignals' not in suite
```

## P7. "Output row/line counts"

Defect class: missing rows (ODS 0 rows → limits undefined at run), truncated
generation.

```python
assert n_ods_data_rows >= n_flow_groups * 2   # both path forms
assert unique_test_numbers == n_rows
```

## Usage rules

1. **One defect → one assertion**: after fixing, add the assert that would have
   caught it. Run it against the OLD artifact to prove it fails (RED), then
   against the new (GREEN).
2. **Deterministic first**: prefer grep/schema/range asserts over LLM judges.
   LLM judges only for semantic judgment with no mechanical formulation.
3. **Assertions are the regression suite**: they persist across rounds; a later
   fix that re-breaks an old defect is caught immediately.
4. **Assert failure = exit non-zero** (run_evals.py contract).
