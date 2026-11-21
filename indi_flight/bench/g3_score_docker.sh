#!/bin/bash
# Run the G3 scorer in the px4-indi-sim image (scipy, pyulog present). Usage (any cwd): bash indi_flight/bench/g3_score_docker.sh RESULTS_DIR
# RESULTS_DIR is repo-relative or absolute; it holds run_NNN/ with flight.ulg, run.json, metrics.json, g3_draw.json.
set -euo pipefail
R=$(cd "$(dirname "$0")/../.." && pwd)
D=$(cd "${1:?RESULTS_DIR}" && pwd)
exec "$R/indi_project/docker/run.sh" -n g3score -t 900 -- bash "$R/indi_flight/bench/g3_score.sh" "$D"
