#!/usr/bin/env bash
# One command per Gate G1 item (GATES.md "G1 Evidence integrity"). Exit 0 pass, 1 fail, 2 not implemented.
#   gate_g1.sh g1.1 RUN_DIR...   gate_g1.sh g1.3 [SET_DIR]   gate_g1.sh g1.4   gate_g1.sh g1.6 BATCH_DIR
set -euo pipefail
B="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R="$(cd "$B/.." && pwd)/results"
item="${1:-}"
[ $# -gt 0 ] && shift
case "$item" in
g1.1)
  [ $# -ge 1 ] || { echo "usage: gate_g1.sh g1.1 RUN_DIR..." >&2; exit 2; }
  python3 "$B/g1_checks.py" g1.1 "$@" ;;
g1.3)
  python3 "$B/g1_checks.py" g1.3 "${1:-$R/det_g16_w125}" ;;
g1.4)
  rc=0
  if python3 -c "import pytest" 2>/dev/null; then
    python3 -m pytest -q "$B/tests" || rc=1
  else
    echo "pytest not available, running each test file with python3"
    for f in "$B"/tests/test_*.py; do echo "-- $f"; python3 "$f" || rc=1; done
  fi
  echo "-- a11_effort_rate.py --selftest"; python3 "$B/a11_effort_rate.py" --selftest || rc=1
  echo "-- second_key_traj.py --selftest"; python3 "$B/second_key_traj.py" --selftest || rc=1
  echo "-- g1_checks.py selftest"; python3 "$B/g1_checks.py" selftest || rc=1
  echo "Metric / identification scripts in bench/ WITHOUT a self-test:"
  for n in disturbance model_variant t3_analyze timebase_check second_key_window g16_spread check_rates; do
    echo "  - $n.py"
  done
  echo "(metrics.py -> tests/test_metrics.py, applied_timing.py -> tests/test_applied_timing.py; runner, plot, fly and batch scripts are not metric scripts)"
  if [ $rc -eq 0 ]; then echo "G1.4 verdict: existing tests PASS, coverage INCOMPLETE (list above)"; else echo "G1.4 verdict: FAIL"; fi
  exit $rc ;;
g1.6)
  [ $# -eq 1 ] || { echo "usage: gate_g1.sh g1.6 BATCH_DIR" >&2; exit 2; }
  tmp="$(mktemp)"
  G16_ROOT="$(cd "$1" && pwd)" G16_SPREAD_OUT="$tmp" python3 "$B/g16_spread.py"
  rc=0
  python3 "$B/g1_checks.py" g1.6a "$tmp" || rc=1
  rm -f "$tmp"
  exit $rc ;;
g1.2|g1.5)
  echo "not implemented: needs simulator work (stage 1)"; exit 2 ;;
*) echo "usage: gate_g1.sh g1.1|g1.2|g1.3|g1.4|g1.5|g1.6 [args]" >&2; exit 2 ;;
esac
