#!/usr/bin/env bash
# Host-side batch driver: scenario x controller x seed x speed, one docker container per run, then metrics.
#
# Usage: indi_project/bench/run_batch.sh
#   SCENARIOS="step_roll hover"  CONTROLLERS="pid_default"  SEEDS="1"  SPEEDS="1 4"  TIMEOUT=600  JOBS=1
# Output: indi_project/results/runs/<scenario>/<controller>/seed<N>[_x<speed> when speed != 1]/
#   (flight.ulg, run.json, metrics.json, px4.log, gz.log, runner.log)
# A controller's parameter overlay is indi_project/bench/params/<controller>.params (lines "NAME VALUE"), optional.
# Each run uses `docker/run.sh -N` (own loopback-only network namespace) so PX4/gz/MAVLink ports never collide;
# runs can therefore run in parallel (JOBS>1) without touching the instance number.
set -u

BENCH_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJ_DIR=$(cd "${BENCH_DIR}/.." && pwd)
RUNSH=${PROJ_DIR}/docker/run.sh
RESULTS=${RESULTS_DIR:-${PROJ_DIR}/results/runs}
# Optional overrides used by bench/tune.py (all unset = default behaviour):
#   PARAMS_FILE  explicit parameter overlay file (instead of bench/params/<controller>.params)
#   RESULTS_DIR  output root (default indi_project/results/runs)
#   FLAT_LAYOUT=1  output <RESULTS_DIR>/<scenario>/seed<N>[_x<speed>] (no <controller> directory)
#   NAME_TAG     suffix appended to the container name (unique names for parallel batches)

SCENARIOS=${SCENARIOS:-"step_roll hover"}
CONTROLLERS=${CONTROLLERS:-"pid_default"}
SEEDS=${SEEDS:-"1"}
SPEEDS=${SPEEDS:-"1 4"}
TIMEOUT=${TIMEOUT:-600}
JOBS=${JOBS:-1}

run_one() { # scenario controller seed speed
	local scn=$1 ctl=$2 seed=$3 speed=$4
	local sfx="" tag=""
	[ "${speed}" != "1" ] && { sfx="_x${speed}"; tag="-x${speed}"; }
	local out="${RESULTS}/${scn}/${ctl}/seed${seed}${sfx}"
	[ "${FLAT_LAYOUT:-0}" = "1" ] && out="${RESULTS}/${scn}/seed${seed}${sfx}"
	tag="${tag}${NAME_TAG:+-${NAME_TAG}}"
	local cname="px4-indi-${scn}-${seed}${tag}"
	local params_arg=()
	[ -f "${BENCH_DIR}/params/${ctl}.params" ] && params_arg=(--params "${BENCH_DIR}/params/${ctl}.params")
	[ -n "${PARAMS_FILE:-}" ] && params_arg=(--params "${PARAMS_FILE}")

	# stale container of the same name (from an earlier aborted batch)?
	if docker ps -a --format '{{.Names}}' | grep -qx "${cname}"; then
		echo "[batch] removing stale container ${cname}"
		docker stop -t 10 "${cname}" > /dev/null 2>&1
		docker rm -f "${cname}" > /dev/null 2>&1
	fi

	mkdir -p "${out}"
	echo "[batch] $(date +%T) start ${scn}/${ctl}/seed${seed} speed=${speed} -> ${out}"
	"${RUNSH}" -n "${scn}-${seed}${tag}" -t "${TIMEOUT}" -N \
		python3 "${BENCH_DIR}/run_scenario.py" --scenario "${scn}" --controller "${ctl}" --seed "${seed}" \
		--speed "${speed}" --out "${out}" ${SIM_VERSION:+--sim "${SIM_VERSION}"} "${params_arg[@]}" > "${out}/runner.log" 2>&1
	local rc=$?
	if [ -f "${out}/flight.ulg" ]; then
		python3 "${BENCH_DIR}/metrics.py" "${out}/flight.ulg" >> "${out}/runner.log" 2>&1 || { echo "[batch] metrics FAILED for ${out}"; rc=1; }
	else
		rc=1
	fi
	echo "[batch] $(date +%T) done  ${scn}/${ctl}/seed${seed} speed=${speed} rc=${rc}"
	return ${rc}
}

fail=0
pids=()
for scn in ${SCENARIOS}; do
	for ctl in ${CONTROLLERS}; do
		for seed in ${SEEDS}; do
			for speed in ${SPEEDS}; do
				run_one "${scn}" "${ctl}" "${seed}" "${speed}" &
				pids+=($!)
				if [ "${#pids[@]}" -ge "${JOBS}" ]; then
					for p in "${pids[@]}"; do wait "$p" || fail=1; done
					pids=()
				fi
			done
		done
	done
done
for p in "${pids[@]}"; do wait "$p" || fail=1; done
echo "[batch] finished, failures=${fail}"
exit ${fail}
