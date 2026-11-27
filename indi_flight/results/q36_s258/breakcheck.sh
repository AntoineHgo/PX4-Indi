#!/usr/bin/env bash
# Break-check of the four unit tests: mutate IndiErpmArmingCheck.cpp, build, run the test binary, restore.
# Run inside the container: indi_project/docker/run.sh -t 1500 'indi_flight/results/q36_s258/breakcheck.sh'
set -u
SRC=src/modules/mc_indi_rate_control/IndiErpmArmingCheck.cpp
BAK=indi_flight/results/q36_s258/IndiErpmArmingCheck.cpp.orig
BIN=build/px4_sitl_test/functional-IndiErpmArmingCheck
cp "$SRC" "$BAK"
trap 'cp "$BAK" "$SRC"' EXIT

run_case() {
	local name=$1 expr=$2
	cp "$BAK" "$SRC"
	sed -i "$expr" "$SRC"
	if cmp -s "$BAK" "$SRC"; then echo "CASE $name: mutation did not apply"; return; fi
	echo "=== CASE $name: $expr"
	diff "$BAK" "$SRC"
	ninja -C build/px4_sitl_test functional-IndiErpmArmingCheck > /dev/null 2>&1 || { echo "build failed"; return; }
	"$BIN" 2>&1 | grep -E "^\[  (FAILED|PASSED)|OK \]|FAILED \]"
}

run_case a_fresh_can_arm 's/if (result.valid && /if (false \&\& /'
run_case b_missing_motor 's/if (result.valid && /if (/'
run_case c_stale 's# && IndiMeasuredTorque::isSampleFresh(now_us, result.timestamp_sample, timeout_s)##'
run_case d_armed 's/if (armed || !measured.enabled())/if (!measured.enabled())/'

cp "$BAK" "$SRC"
ninja -C build/px4_sitl_test functional-IndiErpmArmingCheck > /dev/null 2>&1
echo "=== RESTORED"
"$BIN" 2>&1 | grep -E "^\[  (FAILED|PASSED)|OK \]|FAILED \]"
