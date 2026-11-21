#!/usr/bin/env bash
# S163 outer freeze cells, serial. z: PT 0/1 x 800/400 x seeds 1,2; xy: PT 0/1 x AX 1/2 x 800/400 x seeds 1,2.
# First 2 cells = pre-test: abort (O-12) if their margins json is empty.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/g2_outer_freeze_s163
i=0
run() { bash $D/fly.sh "$@"; N=pt$1_ax$2_r$3_s$4; echo "$(date +%H:%M:%S) $N json=$(wc -c < $D/${N}_margins.json)";
  if [ $i -lt 2 ] && [ ! -s $D/${N}_margins.json ]; then echo ABORT_PRETEST; exit 12; fi; i=$((i+1)); }
for c in "1 3 800 1" "0 3 800 1" "1 3 400 1" "0 3 400 1" "1 3 800 2" "0 3 800 2" "1 3 400 2" "0 3 400 2"; do run $c; done
export AMP=0.08 TP=20 SCN=hover_xlong
for s in 1 2; do for r in 800 400; do for ax in 1 2; do for pt in 1 0; do run $pt $ax $r $s; done; done; done; done
echo OUTER_END
