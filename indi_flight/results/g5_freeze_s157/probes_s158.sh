#!/usr/bin/env bash
# S158 probes (not gate evidence), serial after PID_REF_END. Repo root.
# p1: firmware-default acro cell with ID_OK 1 -> is the G5.1 fwdef FAIL the 0.5x K gate? p2: PID o1 s1 at the freeze plant (F-5, Q11).
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157
until grep -q PID_REF_END $D/batch_status.txt; do sleep 60; done
[ -f $D/stick_steps_s1_fwdef_idok1_acro/flight.ulg ] || { EXPECT=1 TAGX=_fwdef_idok1_acro bash $D/fly.sh stick_steps 1 --stick-mode acro --stick-pilot --params $D/params_fwdef_idok1.params >> $D/batch_status.txt 2>&1
  python3 indi_flight/bench/g51_check.py $D/stick_steps_s1_fwdef_idok1_acro > $D/stick_steps_s1_fwdef_idok1_acro.check.txt 2>&1; }
T=o1_lemniscate_s1_pid
[ -f $D/$T/flight.ulg ] || { docker ps -q --filter name=s157 | xargs -r docker stop >/dev/null
  timeout 1000 indi_project/docker/run.sh -n s157$T -t 900 -- python3 indi_flight/bench/run_scenario.py --controller pid_default \
  --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --scenario o1_lemniscate --out $D/$T > $D/$T.stdout.log 2>&1; echo "fly $T rc=$?" >> $D/batch_status.txt
  python3 indi_flight/bench/g55_check.py $D/$T --json $D/$T/g55.json > $D/$T.check.txt 2>&1; }
echo PROBES_S158_END >> $D/batch_status.txt
