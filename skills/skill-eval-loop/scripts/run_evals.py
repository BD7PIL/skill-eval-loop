#!/usr/bin/env python3
"""Grader-pyramid executor for skill dry-run rounds (skill-eval-loop).

L1 static asserts  : grep/schema checks against generated artifacts (sec)
L2 syntax check    : SSF/LSP diagnostics via bridge (sec-min, no Eclipse needed for SSF)
L3 real build      : bridge build rebuild + getMarkers == 0 errors (min)
L4 run + results   : bridge activate + run + getTestResults all PASSED (min)
                     — the ONLY pass definition

Generic: device name is derived from .project_config.json (or --device).
L1 default asserts come from the assertion pattern library (assertions.md);
override/extend via --assert-file <json>.

Usage:
  python3 run_evals.py <project_root> <prog> [--device NAME] [--skip L1 L2 L3 L4]
                       [--assert-file asserts.json] [--bridge /path/to/eclipse_bridge.py]

<prog> = path to the .prog file relative to the WORKSPACE (the bridge run command
needs the project folder prefix), e.g. MyDevice/src/MyDevice/TestProgram/MyT10.prog.
A project-relative path (src/MyDevice/...) is auto-normalized to workspace-relative.
Exit code: 0 = all green, 1 = any fail. Python 3.6 compatible (no f-strings,
no capture_output, no text=True).
"""
import json
import os
import re
import subprocess
import sys
import time

DEFAULT_BRIDGE = os.path.expanduser('~/bin/st8-dsl-lsp/eclipse_bridge.py')

FAILS = []


def fail(tier, msg):
    FAILS.append((tier, msg))
    print('[FAIL] L%s: %s' % (tier, msg))


def ok(msg):
    print('[ok] %s' % msg)


def run_cmd(cmd, timeout=120, shell=False, cwd=None):
    """Run command, return (exit_code, stdout_text).
    cmd may be a list (no shell) or a string (shell=True)."""
    try:
        if isinstance(cmd, str):
            shell = True
        p = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, cwd=cwd)
        out, err = p.communicate(timeout=timeout)
        return p.returncode, (out + err).decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        return -1, 'TIMEOUT after %ds' % timeout


def find_file(project, pattern):
    """Glob under project/src, return first match or None."""
    import glob
    hits = glob.glob(os.path.join(project, 'src', '**', pattern), recursive=True)
    return hits[0] if hits else None


def derive_device(project, explicit):
    if explicit:
        return explicit
    cfg = os.path.join(project, '.project_config.json')
    if os.path.isfile(cfg):
        try:
            d = json.load(open(cfg))
            if d.get('device'):
                return d['device']
        except Exception:
            pass
    return 'Device'  # fallback; bridge may still resolve by project


# ---------------------------------------------------------------------------
# L1: static asserts (defaults = assertion pattern library instances)
# ---------------------------------------------------------------------------
def l1_static(project, assert_file):
    print('=== L1 static asserts ===')
    # P1: no src/src double path
    if os.path.isdir(os.path.join(project, 'src/src')):
        fail(1, 'src/src double path exists')
    else:
        ok('no src/src')
    # P1: no TODO_LLM residue in generated DSL
    todo = []
    for root, _, files in os.walk(os.path.join(project, 'src')):
        for f in files:
            if f.endswith(('.flow', '.spec', '.dbd')):
                for ln, line in enumerate(open(os.path.join(root, f), encoding='utf-8', errors='replace'), 1):
                    if 'TODO_LLM' in line:
                        todo.append('%s:%d' % (f, ln))
    if todo:
        fail(1, 'TODO_LLM residue: %s' % todo[:3])
    else:
        ok('no TODO_LLM residue')
    # P4: spec level props carry units (typed quantities), if any spec exists
    spec = find_file(project, '*.spec')
    if spec:
        bad = []
        for ln, line in enumerate(open(spec, encoding='utf-8', errors='replace'), 1):
            m = re.search(r'level\.(vrange|irange|iclamp|vforce|waitTime)\s*=\s*([0-9.Ee+-]+)\s*;', line)
            if m and not re.search(r'[VAms]', m.group(2)):
                bad.append((ln, line.strip()))
        if bad:
            fail(1, 'spec bare numbers (need units): %s' % bad[:3])
        else:
            ok('spec level units')
    # P5: flows must not carry active parametricTestDescriptor limits
    flows = []
    for root, _, files in os.walk(os.path.join(project, 'src')):
        for f in files:
            if f.endswith('.flow'):
                flows.append(os.path.join(root, f))
    active_lim = []
    for f in flows:
        for ln, line in enumerate(open(f, encoding='utf-8', errors='replace'), 1):
            s = line.strip()
            if 'parametricTestDescriptor' in s and '=' in s and not s.startswith('//'):
                active_lim.append('%s:%d' % (os.path.basename(f), ln))
    if active_lim:
        fail(1, 'flow has active limits (must be ODS-only): %s' % active_lim[:3])
    else:
        ok('flows have no active limits (ODS-only)')
    # P2: ODS structure (if a testtable exists)
    ods = find_file(project, '*_testtable.ods')
    if ods:
        import zipfile
        with zipfile.ZipFile(ods) as z:
            content = z.read('content.xml').decode('utf-8', 'ignore')
        sheets = set(re.findall(r'table:table table:name="([^"]+)"', content))
        need = {'Tests', 'Profile', 'Alarm_Config', 'STDF_Config',
                'Hardware_Bins', 'Software_Bins', 'TextDatalog_Config'}
        if not need.issubset(sheets):
            fail(1, 'ODS missing sheets: %s' % (need - sheets))
        else:
            ok('ODS 7 sheets')
        m = re.search(r'<table:table table:name="Software_Bins".*?</table:table>', content, re.DOTALL)
        cells = re.findall(r'<text:p[^>]*>([^<]*)</text:p>', m.group(0)) if m else []
        if cells[:6] != ['Software Bin Name', 'Software Bin', 'Hardware Bin',
                         'Result', 'Color', 'Priority']:
            fail(1, 'Software_Bins headers wrong: %s' % cells[:6])
        else:
            ok('Software_Bins 6 cols')
        m = re.search(r'<table:table table:name="Tests".*?</table:table>', content, re.DOTALL)
        rows = re.findall(r'<table:table-row[^>]*>.*?</table:table-row>', m.group(0), re.DOTALL) if m else []
        data = [r for r in rows if 'signalGroup[' in r or 'dpsSignalGroup[' in r]
        if len(data) < 4:
            fail(1, 'ODS has only %d data rows (<4)' % len(data))
        else:
            ok('ODS %d data rows' % len(data))
        # P4: no ±MAX placeholder limits
        pmax = [r for r in data if '1.7976931348623157E308' in r]
        if pmax:
            fail(1, 'ODS has %d +/-MAX placeholder limit rows' % len(pmax))
        else:
            ok('ODS no +/-MAX placeholders')
    # Custom asserts from --assert-file (JSON list of {"name","cmd","expect_fail"})
    if assert_file and os.path.isfile(assert_file):
        with open(assert_file) as f:
            asserts = json.load(f)
        for a in asserts:
            rc, out = run_cmd(a['cmd'], timeout=a.get('timeout', 60), cwd=project)
            failed = (rc != 0)
            if a.get('expect_fail') is not None:
                failed = (failed != bool(a['expect_fail']))
            if failed:
                fail(1, 'custom assert %s: rc=%d %s' % (a['name'], rc, out[-200:]))
            else:
                ok('custom assert %s' % a['name'])


# ---------------------------------------------------------------------------
# L2: syntax check (SSF local diagnostics; no Eclipse needed)
# ---------------------------------------------------------------------------
def l2_syntax(project, bridge):
    print('=== L2 syntax (SSF) ===')
    dsl = []
    for root, _, files in os.walk(os.path.join(project, 'src')):
        for f in files:
            if f.endswith(('.flow', '.spec', '.dbd', '.prog', '.seq')):
                dsl.append(os.path.join(root, f))
    clean = 0
    for f in dsl:
        rc, out = run_cmd([sys.executable, bridge, 'ssf', 'diag', '--root', project, '--file', f], timeout=60)
        if rc != 0 or 'error' in out.lower() and '0 errors' not in out.lower():
            fail(2, 'SSF diag: %s' % f)
            continue
        clean += 1
    if clean == len(dsl) and dsl:
        ok('SSF clean %d files' % len(dsl))
    elif not dsl:
        fail(2, 'no DSL files found under src/')


# ---------------------------------------------------------------------------
# L3: real build (bridge build rebuild + markers)
# ---------------------------------------------------------------------------
def l3_build(project, device, bridge):
    print('=== L3 build (Eclipse) ===')
    rc, out = run_cmd([sys.executable, bridge, device, 'build', 'rebuild', '--skip-guard'], timeout=240)
    if rc != 0 or ('error' in out.lower() and 'built:' not in out):
        fail(3, 'build failed: %s' % out[-300:])
        return
    time.sleep(15)
    rc, out = run_cmd([sys.executable, bridge, device, 'getMarkers'], timeout=90)
    raw = out
    i = raw.find('[')
    markers = json.loads(raw[i:]) if i >= 0 else []
    errs = [m for m in markers if m.get('severity') == 2]
    if errs:
        fail(3, '%d errors: %s' % (len(errs), errs[0].get('message', '')[:120]))
    else:
        ok('compile 0 errors (%d markers)' % len(markers))


# ---------------------------------------------------------------------------
# L4: run + results (the only pass definition)
# ---------------------------------------------------------------------------
def l4_run(project, device, bridge, prog):
    print('=== L4 run (offline) ===')
    run_cmd([sys.executable, bridge, device, 'activate', prog], timeout=240)
    rc, out = run_cmd([sys.executable, bridge, device, 'run', prog], timeout=300)
    raw = out
    i = raw.find('{')
    try:
        d = json.loads(raw[i:]) if i >= 0 else {}
    except Exception:
        d = {}
    if d.get('status') != 'ok':
        fail(4, 'run status: %s' % d.get('message', out[-300:]))
        return
    ok('run ok')
    time.sleep(2)
    rc, out = run_cmd([sys.executable, bridge, device, 'getTestResults', 'Main', 'signal'], timeout=180)
    raw = out
    lines = raw.split('\n')
    fails = [l for l in lines if re.search(r'\sFAIL\s', l)]
    no_lim = [l for l in lines if re.search(r'\d+\s+(PASS|FAIL)\s', l) and '[low=' not in l]
    total = len([l for l in lines if re.search(r'\d+\s+(PASS|FAIL)\s', l)])
    if total == 0:
        fail(4, 'no result rows in getTestResults output')
        return
    if fails:
        fail(4, '%d FAILED rows, first: %s' % (len(fails), fails[0].strip()[:120]))
    if no_lim:
        fail(4, '%d rows without limits, first: %s' % (len(no_lim), no_lim[0].strip()[:120]))
    if not fails and not no_lim:
        ok('all %d rows PASSED with limits' % total)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    project = sys.argv[1]
    prog = sys.argv[2]
    device = None
    bridge = DEFAULT_BRIDGE
    assert_file = None
    skip = set()
    i = 3
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--device' and i + 1 < len(sys.argv):
            device = sys.argv[i + 1]
            i += 2
        elif a == '--bridge' and i + 1 < len(sys.argv):
            bridge = sys.argv[i + 1]
            i += 2
        elif a == '--assert-file' and i + 1 < len(sys.argv):
            assert_file = sys.argv[i + 1]
            i += 2
        elif a == '--skip':
            # collect all following tier tokens (L1..L4), then continue parsing
            # other options that may follow
            j = i + 1
            while j < len(sys.argv) and sys.argv[j].startswith('L'):
                skip.add(sys.argv[j])
                j += 1
            i = j
        else:
            i += 1
    device = derive_device(project, device)
    # L4 needs a workspace-relative .prog path (project folder prefix). Accept
    # a project-relative path too and normalize it (see <prog> in usage).
    if not prog.startswith(device + '/'):
        prog = device + '/' + prog
    print('project=%s device=%s bridge=%s' % (project, device, os.path.basename(bridge)))
    if 'L1' not in skip:
        l1_static(project, assert_file)
    if 'L2' not in skip:
        l2_syntax(project, bridge)
    if 'L3' not in skip:
        l3_build(project, device, bridge)
    if 'L4' not in skip:
        l4_run(project, device, bridge, prog)
    print()
    if FAILS:
        print('EVALS FAILED: %d' % len(FAILS))
        sys.exit(1)
    print('EVALS PASSED (L1-L4)')


if __name__ == '__main__':
    main()
