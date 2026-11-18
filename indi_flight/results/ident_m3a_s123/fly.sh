cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/ident_m3a_s123
p=$1
indi_project/docker/run.sh -n s123id$p -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --sim v2 --params $D/inj_pos$p.params --out $D/pos$p 2>&1 | tail -n 30
