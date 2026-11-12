"""Run the existing offline tests and report a minimal public CI summary.

The GitHub Actions runner uses this to expose diagnostic status when the
collector is blocked before it can publish new sales-detail fields.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'public' / 'data' / 'ci_test_status.json'


def summarize(output, returncode):
    count = re.search(r'Ran (\d+) tests? in ', output)
    failures = re.findall(r'^(?:FAIL|ERROR): (.+)$', output, flags=re.M)
    return {
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'result': 'passed' if returncode == 0 else 'failed',
        'tests_run': int(count.group(1)) if count else None,
        'failure_count': len(failures),
        'failed_tests': [f[:200] for f in failures[:25]],
        'error_excerpt': output[-3000:] if returncode else '',
        'reported_commit': os.environ.get('GITHUB_SHA', '')[:40],
        'note': 'CI test result only; no permit or sales lead is validated by test success.',
    }


def main():
    process = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=240)
    output = (process.stdout or '') + (process.stderr or '')
    print(output[-12000:])
    report = summarize(output, process.returncode)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result':report['result'], 'tests':report['tests_run'],
                      'failures':report['failed_tests']}))
    return process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
