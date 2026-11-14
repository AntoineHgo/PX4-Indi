#!/usr/bin/env bash
# Same-load control for the v1 regression: the OLD binary (build/px4_sitl_default, INDI in mc_rate_control) re-flown
# on step_yaw and step_roll, seeds 1-3, beside the v2 sets, to tell a binary difference from a CPU-load difference
# (the indi_frz reference flew beside r1f with 12 parallel sims).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_o11_regress
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/build/px4_sitl_default
for s in step_yaw step_roll; do
	for seed in 1 2 3; do
		out=$D/runs/v1old/$s/seed$seed
		mkdir -p $out
		( indi_project/docker/run.sh -n o11-v1old-$s-$seed -t 600 -N -e PX4_INDI_BUILD=$B python3 \
			indi_project/bench/run_scenario.py --scenario $s --controller indi_v1old --seed $seed --speed 4 --out $out \
			--params $D/indi_frz.params > $out/runner.log 2>&1
		  python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
		  echo "[v1old] $(date +%T) done $s seed$seed" ) &
	done
	wait
done
echo O11_V1OLD_DONE
