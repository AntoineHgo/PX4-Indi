#!/usr/bin/env bash
# S157 stage-6 freeze re-fly (D-FREEZE-6): quad5in defaults + runner ID_OK 1 overlay, matched GNSS 110 ms,
# G4 typical profile (D-NOISE-PROF). Repo root. Usage: fly.sh <scenario> <seed> [extra runner args...]
set -u
D=indi_flight/results/g5_freeze_s157
SC=$1; SEED=$2; shift 2
TAG=${SC}_s${SEED}${TAGX:-}
docker ps -q --filter name=s157 | xargs -r docker stop >/dev/null
timeout 1000 indi_project/docker/run.sh -n s157$TAG -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
  --model quad5in --seed $SEED --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
  --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --params $D/params.params --scenario $SC "$@" --out $D/$TAG > $D/$TAG.stdout.log 2>&1
echo "fly $TAG rc=$?"
