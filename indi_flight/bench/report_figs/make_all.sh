#!/usr/bin/env bash
# Draw every report figure into indi_flight/report/pdf/figures/ from committed results. Works from any cwd.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
for s in fig_g2_margins fig_g2_bode_rate fig_steps fig_g3_campaign fig_g4_noise fig_g5_modes fig_limits; do
    python3 "$s.py"
done
# optional: regenerate results/report_traces/*.csv from the original (untracked) logs, only where they still exist
#   python3 extract_traces.py
