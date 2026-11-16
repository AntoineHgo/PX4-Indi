#!/bin/bash
# G1.6 re-fly after the baro fixes (4443079c0b elevation, 4297ba9869 A-20 atomic ref), S32.
# Pretest: 1 hover at speed 4, stop unless |bias0| < 0.5 m and baro_fault 0 (a14_close_check.py).
# Then hover, step_roll, traj_lemniscate x5 identical seeds, --sched --sched-anchor, speed 4 then 1.
# Sequential, -t 300 wall timeout per run, no retry (a failure is data). Ends with a14_close_check over every log (A-20 test).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
B=indi_flight/results/g16_set_s32
mkdir -p $B
fly() { # speed scenario run outdir
  t0=$(date +%s)
  indi_project/docker/run.sh -n g16s32_s$1_$2_$3 -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario $2 --controller pid_default --model quad5in --seed 1 --speed $1 --sched --sched-anchor --out $4 > $4_stdout.log 2>&1
  echo "s$1 $2 $3 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $B/status.txt
}
mkdir -p $B/pretest
fly 4 hover r1 $B/pretest/hover_r1
python3 indi_flight/bench/a14_close_check.py --out $B/pretest/check.md $B/pretest/hover_r1/flight.ulg > /dev/null 2>&1
if ! python3 - $B/pretest/check.md <<'PY'
import sys
rows=[l.split('|') for l in open(sys.argv[1]) if l.startswith('| indi_flight')]
ok=rows and all(abs(float(r[4]))<0.5 and r[7].strip()=='0' for r in rows)
sys.exit(0 if ok else 1)
PY
then echo "PRETEST_FAIL" >> $B/status.txt; exit 1; fi
echo "PRETEST_PASS" >> $B/status.txt
for sp in 4 1; do
  R=$B/speed$sp
  for sc in hover step_roll traj_lemniscate; do
    mkdir -p $R/$sc
    for r in r1 r2 r3 r4 r5; do fly $sp $sc $r $R/$sc/$r; done
  done
  echo "BATCH_DONE speed$sp" >> $B/status.txt
done
python3 indi_flight/bench/a14_close_check.py --out $B/a20_check.md $B/speed*/*/r*/flight.ulg > /dev/null 2>&1
echo "ALL_DONE a20_check_rc=$?" >> $B/status.txt
