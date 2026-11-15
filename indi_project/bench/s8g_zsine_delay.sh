#!/usr/bin/env bash
# Stage-8 review finding 2: INDI POS on diag_z_multisine (diagnostic vertical multisine, outside T/H/V) for the a_f / t_f lag
# identification (bench/ident_s8_delay.py). Diagnostic, not part of any verdict. Uses the binary already built.
# Ends S8G_ZSINE_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
out=$P/results/s8g_zsine_delay/seed1
mkdir -p $out
indi_project/docker/run.sh -n s8g-fly -t 600 -N python3 indi_project/bench/run_scenario.py --scenario diag_z_multisine \
	--controller indi_pos_v0 --seed 1 --speed 1 --out $out --sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 \
	--vib-gyr 0.05 --params $P/bench/params/indi_pos_v0.params > $out/runner.log 2>&1
python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
python3 indi_project/bench/ident_s8_delay.py $out/flight.ulg 1 > $out/delay.txt 2>&1
echo S8G_ZSINE_DONE
