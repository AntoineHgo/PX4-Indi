#!/usr/bin/env bash
# G3 candidate (iii) S235: rate integrator, 4 pass-line draws, event hover scenario, sequential.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
S=indi_flight/results/g3_cand_iii_s235
ST=$S/STATUS.txt
PARAMS=$S/cand_iii.params
R=indi_flight/results/g3_refly_actc_s212
fly() { # NAME IDX [SAMPLES]
	local n=$1 i=$2 sm=${3:-} t0 rc
	t0=$(date '+%F %T'); echo "$t0 START $n" >>$ST
	timeout 1700 indi_flight/results/g3_cand_iii_s235/run_flight.sh -e PX4_INDI_BUILD=/tmp/px4_cand_iii/build/px4_sitl_default -n g3s235_$n -t 1500 -- \
		python3 indi_flight/bench/g3_run.py --seed 173 --n 300 --start $i --stop $i \
		--base-params $PARAMS --out-root $S/$n --timeout-s 1200 --speed 1 \
		${sm:+--samples $sm --require-actc} >$S/stream_$n.txt 2>&1
	rc=$?; echo "$t0 -> $(date '+%F %T') END $n exit=$rc" >>$ST
}
fly joint 24 $R/restore264/samples_joint
fly d264 24 $R/samples
fly d262 22 $R/samples
fly d283 283
echo "$(date '+%F %T') CHAIN_FINISHED" >>$ST
