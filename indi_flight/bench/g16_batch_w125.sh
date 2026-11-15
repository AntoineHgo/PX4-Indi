#!/bin/bash
# G1.6 short repeat on the 1.25 ms world (D-SIM-STEP, S16), rate 800, logger -p actuator_motors. traj r1 first = pre-test.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
mkdir -p indi_flight/results/det_g16_w125
R=indi_flight/results/det_g16_w125
STATUS=$R/status.txt
run_one() {  # scenario rN attempt
  local sc=$1 rn=$2 att=$3 d=$R/$1/$2
  local name=det_g16w_${sc}_${rn}_a${att}
  local t0=$(date +%s)
  indi_project/docker/run.sh -n $name -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario $sc --controller pid_default --model quad5in --seed 1 --speed 4 --out $d > $R/${sc}_${rn}_a${att}_stdout.log 2>&1
  local rc=$?
  local wall=$(( $(date +%s) - t0 ))
  python3 -I indi_flight/bench/g16_check.py $d $sc > $R/check_${sc}_${rn}_a${att}.txt 2>&1
  local ck=$?
  echo "$sc $rn attempt=$att docker_rc=$rc check_rc=$ck wall=${wall}s" >> $STATUS
  return $ck
}
flight() {  # scenario rN
  if run_one "$1" "$2" 1; then return 0; fi
  # keep the failed attempt aside, then retry once into the same dir
  mv $R/$1/$2 $R/$1/${2}_failed_a1 2>/dev/null
  run_one "$1" "$2" 2 && { echo "$1 $2 RECOVERED on retry" >> $STATUS; return 0; }
  mv $R/$1/$2 $R/$1/${2}_failed_a2 2>/dev/null
  echo "$1 $2 FAILED twice (kept as ${2}_failed_a1, ${2}_failed_a2)" >> $STATUS
  return 1
}
flight traj_lemniscate r1 || { echo "STOP: traj pre-test failed" >> $STATUS; exit 1; }
for r in r1 r2 r3 r4 r5; do flight hover $r; done
for r in r1 r2 r3 r4 r5; do flight step_roll $r; done
for r in r2 r3 r4 r5; do flight traj_lemniscate $r; done
echo BATCH_DONE >> $STATUS
