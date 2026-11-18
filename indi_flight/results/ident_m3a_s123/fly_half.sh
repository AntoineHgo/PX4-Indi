# S125 halved-gain ident flights (roll ax1, yaw ax3), sequential (parallel launch failed S124)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/ident_m3a_s123
for ax in 1 3; do
indi_project/docker/run.sh -n s125half$ax -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --sim v2 --params $D/inj_half_ax$ax.params --out $D/half_ax$ax 2>&1 | tail -n 8
done
