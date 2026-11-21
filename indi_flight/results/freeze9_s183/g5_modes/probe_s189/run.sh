cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=indi_flight/results/freeze9_s183/g5_modes/probe_s189
for t in both ponly vonly; do
  docker ps -q --filter name=s189p_ | xargs -r docker stop >/dev/null 2>&1
  timeout 1000 indi_project/docker/run.sh -n s189p_$t -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    --model quad5in --seed 3 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $P/$t.params --scenario mode_switch10 --stick-mode posctl --out $P/ms10_s3_$t > $P/ms10_s3_$t.stdout.log 2>&1
  echo "$t rc=$?" >> $P/status.txt
  python3 indi_flight/bench/g57_check.py --validity leaveP $P/ms10_s3_$t > $P/ms10_s3_$t.key1.txt 2>&1
done
docker ps -q --filter name=s189p_ | xargs -r docker stop >/dev/null 2>&1
echo DONE >> $P/status.txt
