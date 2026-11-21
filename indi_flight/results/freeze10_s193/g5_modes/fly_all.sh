#!/usr/bin/env bash
# Freeze-10 re-fly of G5.1 / G5.2 / G5.7 (INDI only), serial. Commands = S157 results/g5_freeze_s157/fly.sh + batch.sh/batch2.sh,
# unchanged except the output dir. Resume: rerun this script (runs with flight.ulg are skipped; scoring always re-runs).
# Usage (any cwd): bash indi_flight/results/freeze10_s193/g5_modes/fly_all.sh   SEEDS="1 2 3" by default; NOFLY=1 scores only.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/freeze10_s193/g5_modes
P=indi_flight/results/g5_freeze_s157/params.params   # MC_INDI_EN 1 -> runner aliases MC_RATE_CTL_TYPE 1 (run_scenario.py S131)
B=indi_flight/bench
mkdir -p $D
st() { echo "$(date +%H:%M:%S) $*" >> $D/batch_status.txt; }

# run <tag> <scenario> <seed> [runner args]
run() {
  local tag=$1 sc=$2 seed=$3; shift 3
  [ -f $D/$tag/flight.ulg ] && return
  docker ps -q --filter name=f10modes_ | xargs -r docker stop >/dev/null 2>&1
  timeout 1000 indi_project/docker/run.sh -n f10modes_$tag -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    --model quad5in --seed $seed --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $P --scenario $sc "$@" --out $D/$tag > $D/$tag.stdout.log 2>&1
  st "fly $tag rc=$?"
  # S157 batch.sh assertion: identified gains applied; also record the INDI module start param
  python3 -c "import json,sys;r=json.load(open('$D/$tag/run.json'))['params_applied'];print('$tag ID_OK',r.get('MC_INDI_ID_OK'),'RATE_CTL_TYPE',r.get('MC_RATE_CTL_TYPE'));sys.exit(str(r.get('MC_INDI_ID_OK'))!='1' or str(r.get('MC_RATE_CTL_TYPE'))!='1')" >> $D/batch_status.txt 2>&1 \
    || st "WARN $tag params check failed (ID_OK/RATE_CTL_TYPE not 1) - flight kept, inspect before scoring"
}

if [ -z "${NOFLY:-}" ]; then
  for s in ${SEEDS:-1 2 3}; do
    run stick_steps_s${s}_acro      stick_steps     $s --stick-mode acro       --stick-pilot   # G5.1
    run stick_steps_s${s}_stab      stick_steps     $s --stick-mode stabilized --stick-pilot   # G5.1
    run stick_pos_steps_s${s}_altctl stick_pos_steps $s --stick-mode altctl                    # G5.2
    run stick_pos_steps_s${s}_posctl stick_pos_steps $s --stick-mode posctl                    # G5.2
    run mode_switch10_s${s}         mode_switch10   $s --stick-mode posctl                     # G5.7
  done
  st FLY_DONE
fi

# ---- scoring (S157 checks.sh pattern: host python3 if pyulog imports, else docker)
if python3 -c "import pyulog" 2>/dev/null; then py() { python3 "$@"; }
else py() { indi_project/docker/run.sh -n f10modes_chk -t 240 -- python3 "$@"; }; fi
for s in ${SEEDS:-1 2 3}; do
  for m in acro stab; do t=stick_steps_s${s}_$m; [ -d $D/$t ] || continue
    py $B/g51_check.py $D/$t > $D/$t.key1.txt 2>&1;                    st "key1 $t rc=$?"
    py $B/g51_g52_key2.py g51 $D/$t > $D/$t.key2.txt 2>&1;             st "key2 $t rc=$?"
  done
  for m in altctl posctl; do t=stick_pos_steps_s${s}_$m; [ -d $D/$t ] || continue
    py $B/g52_check.py $D/$t > $D/$t.key1.txt 2>&1;                    st "key1 $t rc=$?"
    py $B/g51_g52_key2.py g52 $D/$t > $D/$t.key2.txt 2>&1;             st "key2 $t rc=$?"
  done
  t=mode_switch10_s$s; [ -d $D/$t ] || continue
  py $B/g57_check.py --validity leaveP $D/$t > $D/$t.key1.txt 2>&1;    st "key1 $t rc=$?"
  py $B/g55_g57_key2.py g57 $D/$t > $D/$t.key2.txt 2>&1;               st "key2 $t rc=$?"
done
st SCORE_DONE
