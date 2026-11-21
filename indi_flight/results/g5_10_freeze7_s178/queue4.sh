#!/usr/bin/env bash
# G5.10 redefined pre-test flights (S178), serial + idempotent (skips a run dir that has flight.ulg; resume = rerun). Repo root irrelevant.
# Order: INDI SAT, INDI STAB, PID SAT, PID STAB (seed 1). Waits for queue.sh (freeze7_s177), queue2.sh, queue3.sh and idle s177*/s178s* containers.
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/g5_10_freeze7_s178; P=indi_flight/results/g5_freeze_s157/params.params
Q1=indi_flight/results/freeze7_s177; Q2=indi_flight/results/g2_outer_freeze7_s177; Q3=indi_flight/results/g2_spot_freeze7_s178
mkdir -p $R; S=$R/queue4_status.tsv; [ -f $S ] || printf 'name\tstart\tend\trc\n' > $S
stamp() { date '+%F %T'; }
ready() {
  grep -q QUEUE_END $Q1/queue.log 2>/dev/null || return 1
  grep -q QUEUE_END $Q2/queue2.log 2>/dev/null || return 1
  # queue3: if its script exists, wait for QUEUE3_END (it also ends on WAIT_TIMEOUT)
  if [ -f $Q3/queue3.sh ]; then grep -q QUEUE3_END $Q3/queue3.log 2>/dev/null || return 1; fi
  [ -z "$(docker ps -q --filter name=s177)" ] && [ -z "$(docker ps -q --filter name=s178s)" ] || return 1
  pgrep -f 'queue[23]?\.sh' >/dev/null && return 1
  return 0
}
echo "wait for queue1/2/3 end and idle containers $(stamp)"
for i in $(seq 480); do ready && break; sleep 30; done   # 480 x 30 s = 4 h
ready || { echo WAIT_TIMEOUT $(stamp); echo QUEUE4_END; exit 2; }
echo "start $(stamp)"
NOISE="--model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
item() { # item <name> <runner args...>   (out dir $R/<name>)
  local n=$1; shift; local o=$R/$n
  [ -f $o/flight.ulg ] && return
  local t0; t0=$(stamp)
  timeout 1000 indi_project/docker/run.sh -n s178g510$n -t 900 -- python3 indi_flight/bench/run_scenario.py $NOISE "$@" --out $o > $o.stdout.log 2>&1
  printf '%s\t%s\t%s\t%s\n' "$n" "$t0" "$(stamp)" $? >> $S
}
item indi_sat_s1  --controller indi --params $P --scenario sat_sustained --scenario-overrides $R/sat_override.json
item indi_stab_s1 --controller indi --params $P --scenario g510_stab_full --stick-mode stabilized
item pid_sat_s1   --controller pid --scenario sat_sustained --scenario-overrides $R/sat_override.json
item pid_stab_s1  --controller pid --scenario g510_stab_full --stick-mode stabilized
echo "end $(stamp)"; echo QUEUE4_END
