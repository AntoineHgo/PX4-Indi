#!/usr/bin/env bash
# G5.7 PID reference flights (S188): mode_switch10 seeds 1-3, stock PID (--controller pid_default, NO --params file so no MC_INDI_EN),
# all other flags identical to fly_all.sh. Serial. Resume: rerun (runs with flight.ulg skipped; scoring always re-runs).
# Usage (any cwd): bash indi_flight/results/freeze9_s183/g5_modes/fly_pid_g57.sh   DRYRUN=1 prints the seed-1 command only.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/freeze9_s183/g5_modes
B=indi_flight/bench
st() { echo "$(date +%H:%M:%S) $*" >> $D/batch_status.txt; }
cmd() { # <seed>
  echo timeout 1000 indi_project/docker/run.sh -n f9g57pid_s$1 -t 900 -- python3 indi_flight/bench/run_scenario.py --controller pid_default \
    --model quad5in --seed $1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --scenario mode_switch10 --stick-mode posctl --out $D/pid_mode_switch10_s$1
}
if [ -n "${DRYRUN:-}" ]; then cmd 1; exit 0; fi
for s in 1 2 3; do
  t=pid_mode_switch10_s$s
  [ -f $D/$t/flight.ulg ] && continue
  docker ps -q --filter name=f9g57pid_ | xargs -r docker stop >/dev/null 2>&1
  $(cmd $s) > $D/$t.stdout.log 2>&1
  st "fly $t rc=$?"
done
st PID_G57_FLY_DONE
if python3 -c "import pyulog" 2>/dev/null; then py() { python3 "$@"; }
else py() { indi_project/docker/run.sh -n f9g57pid_chk -t 240 -- python3 "$@"; }; fi
for s in 1 2 3; do
  t=pid_mode_switch10_s$s; [ -d $D/$t ] || continue
  py $B/g57_check.py --validity leaveP $D/$t > $D/$t.key1.txt 2>&1; st "key1 $t rc=$?"
  py $B/g55_g57_key2.py g57 $D/$t > $D/$t.key2.txt 2>&1;            st "key2 $t rc=$?"
done
st PID_G57_SCORE_DONE
touch $D/PID_G57_DONE
