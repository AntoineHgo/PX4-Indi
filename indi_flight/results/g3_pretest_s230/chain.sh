#!/usr/bin/env bash
# G3 pretest S230: event-hover scenario. Flight only, no scoring. Run from anywhere.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
S=indi_flight/results/g3_pretest_s230
ST=$S/STATUS.txt
PARAMS=indi_flight/results/g5_freeze_s157/params.params
indi() { # NAME IDX
	local n=$1 i=$2 t0 rc
	t0=$(date '+%F %T'); echo "$t0 START $n" >>$ST
	timeout 1700 indi_project/docker/run.sh -n g3s230_$n -t 1500 -- \
		python3 indi_flight/bench/g3_run.py --seed 173 --n 300 --start $i --stop $i \
		--base-params $PARAMS --out-root $S/$n --timeout-s 1200 --speed 1 >$S/stream_$n.txt 2>&1
	rc=$?; echo "$t0 -> $(date '+%F %T') END $n exit=$rc" >>$ST
}
pid() {
	local t0 rc; t0=$(date '+%F %T'); echo "$t0 START pid_d0" >>$ST
	timeout 1800 python3 $S/fly_pid_s230.py >$S/stream_pid_d0.txt 2>&1
	rc=$?; echo "$t0 -> $(date '+%F %T') END pid_d0 exit=$rc" >>$ST
}
indi indi_d0 0
pid
indi indi_d262 262
indi indi_d283 283
echo "$(date '+%F %T') CHAIN_FINISHED" >>$ST
