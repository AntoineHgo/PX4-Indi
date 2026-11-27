#!/usr/bin/env bash
# Break-check of test 7: the arming check is made to allow always, SITL build, same flight: TEST7 must report FAIL.
# Run: indi_project/docker/run.sh -n q37bcs -t 3000 -e PX4_INDI_BUILD=$PWD/build/q36_sitl 'indi_flight/results/q37_s259/breakcheck_sitl.sh'
set -u
R=indi_flight/results/q37_s259
SRC=src/modules/mc_indi_rate_control/IndiErpmArmingCheck.cpp
cp "$SRC" "$R/IndiErpmArmingCheck.cpp.orig"
trap 'cp "$R/IndiErpmArmingCheck.cpp.orig" "$SRC"' EXIT
sed -i 's/^\tif (armed) {$/\tif (true) {/' "$SRC"
diff "$R/IndiErpmArmingCheck.cpp.orig" "$SRC"
ninja -C build/q36_sitl px4 > "$R/sitl_build_mutant.log" 2>&1 || { echo "mutant build failed"; exit 1; }
python3 "$R/arm_refusal_flight.py" --scenario hover --controller indi --seed 1 --speed 3 \
	--params "$R/sitl_params.params" --out "$R/sitl_refusal_mutant"
echo "=== RESTORE and rebuild"
cp "$R/IndiErpmArmingCheck.cpp.orig" "$SRC"
ninja -C build/q36_sitl px4 > "$R/sitl_build_restored.log" 2>&1 && echo restored-build-ok
