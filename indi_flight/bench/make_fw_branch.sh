#!/usr/bin/env bash
# G7(g): build a clean firmware-only branch from local main. Never pushes.
# usage: make_fw_branch.sh [source-ref=feat/indi-flight] [branch=indi-fw-pr] [--force-recreate]
set -euo pipefail

FORCE=0; POS=()
for a in "$@"; do [ "$a" = "--force-recreate" ] && FORCE=1 || POS+=("$a"); done
SRC=${POS[0]:-feat/indi-flight}
BR=${POS[1]:-indi-fw-pr}
REPO=$(git rev-parse --show-toplevel)
WT=${FWBRANCH_WT:-/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/df494851-21e5-4558-aa12-7657cfda1ddd/scratchpad/fwbranch}
cd "$REPO"

# Class A: INDI firmware (explicit paths, no tree-wide globbing)
A_PATHS=(
  src/lib/indi_accel_control
  src/lib/indi_rate_control
  src/modules/mc_indi_rate_control
  src/modules/mc_indi_pos_control
  msg/ActuatorTorqueMeasured.msg
  msg/IndiPosStatus.msg
  msg/IndiRateFeedforward.msg
  msg/IndiRateStatus.msg
  msg/CMakeLists.txt                 # Sim* lines stripped in commit 1
  src/lib/CMakeLists.txt
  src/modules/logger/logged_topics.cpp
  ROMFS/px4fmu_common/init.d/rc.mc_apps
  ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in
  ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt
  boards/px4/sitl/default.px4board   # SIM_SCENARIO_PLAYER line stripped in commit 1
)
# Class B: simulation (separable commit)
B_PATHS=(
  src/modules/simulation/gz_bridge
  src/modules/simulation/sim_scenario_player
  msg/SimGroundTruth.msg
  msg/SimScheduleApplied.msg
  msg/CMakeLists.txt                 # full version
  boards/px4/sitl/default.px4board   # full version
  ROMFS/px4fmu_common/init.d-posix/rcS
)
STOCK=(src/modules/mc_rate_control src/modules/mc_att_control src/modules/mc_pos_control
       src/modules/control_allocator src/lib/control_allocation src/modules/commander)

if git show-ref --verify --quiet "refs/heads/$BR"; then
  if [ $FORCE -eq 1 ]; then git branch -D "$BR"
  else echo "branch $BR exists; use --force-recreate" >&2; exit 1; fi
fi
git rev-parse --verify --quiet "$SRC^{commit}" >/dev/null || { echo "bad source ref $SRC" >&2; exit 1; }

MB=$(git merge-base main "$SRC"); MAIN=$(git rev-parse main)
if [ "$MB" = "$MAIN" ]; then echo "main == merge-base ($MB)"
else
  echo "main has MOVED: main=$MAIN merge-base=$MB"
  echo "A/B paths changed on main since merge-base (conflict candidates):"
  git diff --name-only "$MB" main -- "${A_PATHS[@]}" "${B_PATHS[@]}" || true
fi

[ -e "$WT" ] && { echo "worktree path $WT exists" >&2; exit 1; }
mkdir -p "$(dirname "$WT")"
git worktree add -b "$BR" "$WT" main >/dev/null
trap 'cd "$REPO"; git worktree remove --force "$WT" 2>/dev/null || true' EXIT
cd "$WT"

MSG=$(mktemp)
# ---- commit 1
git checkout "$SRC" -- "${A_PATHS[@]}"
sed -i '/^\tSimGroundTruth\.msg$/d;/^\tSimScheduleApplied\.msg$/d' msg/CMakeLists.txt
sed -i '/CONFIG_MODULES_SIMULATION_SIM_SCENARIO_PLAYER=y/d' boards/px4/sitl/default.px4board
git add -A
cat > "$MSG" <<'M'
feat(indi): INDI rate and acceleration control modules

Add mc_indi_rate_control and mc_indi_pos_control modules with the
indi_rate_control and indi_accel_control libraries, their uORB topics,
logger entries, SITL board config, start-up selection through
MC_INDI_EN and MC_INDI_POS_EN, the quad5in airframe, and unit tests.
Stock controllers are unchanged.

Assisted-by: Claude
M
git commit -q -F "$MSG"
# ---- commit 2
git checkout "$SRC" -- "${B_PATHS[@]}"
git add -A
cat > "$MSG" <<'M'
feat(simulation): gz_bridge rotor-speed telemetry for INDI

Publish rotor-speed (eRPM) telemetry from gz_bridge for the INDI
rate controller, and add the SITL scenario player with its ground
truth and schedule topics.

Assisted-by: Claude
M
git commit -q -F "$MSG"
rm -f "$MSG"

# ---- assertions
OUT1=$(git diff --stat main -- indi_flight indi_project)
OUT2=$(git diff --stat main -- "${STOCK[@]}")
echo "pass rule git diff --stat main -- indi_flight indi_project: [${OUT1}]"
echo "stock-module diff: [${OUT2}]"
[ -z "$OUT1" ] && [ -z "$OUT2" ] || { echo "ASSERTION FAILED" >&2; exit 2; }
echo "--- commits"; git log --oneline main..HEAD
echo "--- diffstat"; git diff --stat main HEAD | tail -1
echo "--- paths in branch not in A/B lists:"
git diff --name-only main HEAD | grep -vE "^($(printf '%s|' "${A_PATHS[@]}" "${B_PATHS[@]}" | sed 's/|$//'))" || echo none
echo "branch $BR created locally (not pushed, build unverified)"
