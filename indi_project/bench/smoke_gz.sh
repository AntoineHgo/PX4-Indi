#!/usr/bin/env bash
# Smoke test, run INSIDE the px4-indi-sim container (via indi_project/docker/run.sh):
# start gz_x500 headless in lockstep, take off, hover, land, shut down.
# Prints wall-clock duration so the speed factor can be checked against sim time
# (sim time comes from the ULog, see the analysis step).
#
# Usage: indi_project/bench/smoke_gz.sh [speed_factor]
set -u

SPEED=${1:-1}
REPO=${PX4_INDI_REPO:-$(pwd)}
BUILD=${REPO}/build/px4_sitl_default
OUT=${REPO}/indi_project/logs/smoke_gz_speed${SPEED}
mkdir -p "${OUT}"

export HEADLESS=1
export PX4_SIM_MODEL=gz_x500
export PX4_SIM_SPEED_FACTOR=${SPEED}

wait_for() { # pattern timeout_s
	for _ in $(seq 1 "$2"); do
		grep -q "$1" "${OUT}/px4.log" && return 0
		sleep 1
	done
	echo "TIMEOUT waiting for: $1"
	return 1
}

t0=$(date +%s.%N)
"${BUILD}/bin/px4" -d -w "${BUILD}/rootfs" "${BUILD}/etc" > "${OUT}/px4.log" 2>&1 &
PX4_PID=$!

# No GCS and no RC in this harness: disable the corresponding failsafes and
# arming checks (identical for every controller under test).
wait_for "Startup script returned successfully" 180
"${BUILD}/bin/px4-param" set NAV_DLL_ACT 0
"${BUILD}/bin/px4-param" set COM_RC_IN_MODE 4
"${BUILD}/bin/px4-param" set COM_RCL_EXCEPT 4

if wait_for "Ready for takeoff" 180; then
	t_ready=$(date +%s.%N)
	"${BUILD}/bin/px4-commander" takeoff
	sleep "$(awk -v s="${SPEED}" 'BEGIN{print 30/s}')"
	"${BUILD}/bin/px4-listener" vehicle_local_position > "${OUT}/hover_lpos.txt" 2>&1
	"${BUILD}/bin/px4-commander" land
	wait_for "Disarmed by landing\|Disarmed by auto preflight" $((120))
	t_end=$(date +%s.%N)
	awk -v a="$t0" -v b="$t_ready" -v c="$t_end" 'BEGIN{printf "wall_ready_s=%.1f wall_flight_s=%.1f\n", b-a, c-b}' | tee "${OUT}/timing.txt"
fi

"${BUILD}/bin/px4-shutdown" > /dev/null 2>&1 || kill "${PX4_PID}"
sleep 3
pkill -f "gz sim" || true
wait "${PX4_PID}" 2> /dev/null
cp "$(ls -t "${BUILD}"/rootfs/fs/log/*/*.ulg 2> /dev/null | head -1)" "${OUT}/" 2> /dev/null || echo "no ulog found"
echo "done, outputs in ${OUT}"
