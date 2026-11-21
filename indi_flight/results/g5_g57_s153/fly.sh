#!/usr/bin/env bash
# S153 G5.7 mode_switch10 seed 1 re-fly with GNSS delay 110 ms on the current firmware (23acbdef67 INDI position module). Repo root.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 1
timeout 900 indi_project/docker/run.sh -n s153s1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario mode_switch10 --stick-mode posctl --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/g5_g57_s153/params.params --gps-dly 110 --gnss-delay 110 --out indi_flight/results/g5_g57_s153/mode_switch10_s1
