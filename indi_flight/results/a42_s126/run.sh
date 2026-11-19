# S126 A-42 closing test: two sequential run.sh calls, distinct -n and out dirs, stock params
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/a42_s126
for k in 1 2; do
indi_project/docker/run.sh -n s126a42_$k -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --sim v2 --out $D/r$k/ > $D/r$k.stdout 2>&1
echo "run $k rc=$? $(date +%T)" >> $D/rc.txt
done
