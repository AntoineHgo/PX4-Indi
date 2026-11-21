#!/usr/bin/env bash
# FREEZE-10 candidate probe, Part A flights. Same commands as freeze9_s183 (queue.sh fly(), g5_modes/fly_all.sh, gate_g4.sh), out dir changed. Serial.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/freeze10_cand_s191; P=indi_flight/results/g5_freeze_s157/params.params
PLANT="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
HARSH="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0"
run() { # tag plant scenario seed extra...
  local tag=$1 pl=$2 sc=$3 sd=$4; shift 4
  [ -f $D/$tag/flight.ulg ] && return
  timeout 1000 indi_project/docker/run.sh -n f10a_$tag -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    $pl --seed $sd --params $P --scenario $sc "$@" --out $D/$tag > $D/$tag.stdout.log 2>&1
  echo "$(date +%H:%M:%S) $tag rc=$?" >> $D/status_a.txt
}
for s in 1 2 3; do run mode_switch10_s$s "$PLANT" mode_switch10 $s --stick-mode posctl; done
run auto_land10_typ_s1 "$PLANT" auto_land10 1
run auto_tour_typ_s1 "$PLANT" auto_tour 1
run auto_tour_harsh_s1 "$HARSH" auto_tour 1
mkdir -p $D/g4
timeout 1000 sh indi_flight/bench/gate_g4.sh fly $D/g4 typ cruise 1
echo "$(date +%H:%M:%S) g4 done" >> $D/status_a.txt
touch $D/FLY_A_DONE
