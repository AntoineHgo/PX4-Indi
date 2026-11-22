#!/usr/bin/env bash
# Detached, resumable, serial flight chain for the G3 campaign (seed 173, n 300, FREEZE-10).
#
#   bash indi_flight/bench/g3_chain.sh start   [DIR] [IDX_FIRST IDX_LAST] [--allow-binary SHA256] [--speed F]
#   bash indi_flight/bench/g3_chain.sh status  [DIR]
#   bash indi_flight/bench/g3_chain.sh stop    [DIR] [--now]
#   bash indi_flight/bench/g3_chain.sh rescore [DIR]
#
# DIR (default indi_flight/results/g3_campaign_f10) must be under indi_flight/results. Range default 0 299, then the
# range of the previous start in DIR. --speed F: sim speed factor (g3_run.py --speed), default 1.0, pinned per DIR. One flight at a time, in index order; a run with run_NNN/g3_done.json is skipped.
# The chain holds indi_flight/logs/flight_chain.lock while it runs: a held lock means "gate flights in progress".
# It ignores indi_flight/STOP (the supervisor's stop file): the chain flies across supervisor stops.
# Per run, same command as results/g3_pretest_q24_s197/fly_all.sh, then both scoring keys as in score_all.sh.
# No git, no Claude. See results/g3_campaign_f10/README.md.
#
# TEST HOOK (smoke tests only): G3_CHAIN_TEST_FLIGHT_CMD="false" replaces the flight command by that shell command.
# It is refused unless DIR's name contains "smoke".
set -u
export LC_NUMERIC=C

REPO=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd) || exit 1
cd "$REPO" || exit 1
SELF=$REPO/indi_flight/bench/g3_chain.sh
LOCK=$REPO/indi_flight/logs/flight_chain.lock
DIRFILE=$REPO/indi_flight/logs/flight_chain.dir # repo-relative DIR of the last started chain
DEFAULT_DIR=indi_flight/results/g3_campaign_f10

# campaign definition (results/g3_pretest_q24_s197/fly_all.sh)
SEED=173
N=300
PARAMS=indi_flight/results/g5_freeze_s157/params.params
FLIGHT_TIMEOUT_S=1700 # host timeout around run.sh
CONTAINER_TIMEOUT_S=1500
RUN_TIMEOUT_S=1200 # g3_run.py --timeout-s
BINARY=build/px4_sitl_default/bin/px4
# FREEZE-10 gate binary: provenance.binary_sha256 of every run in results/g3_pretest_q24_s197/run_*/run.json
FREEZE_BINARY_SHA=d220e19315c2798aa18a1bab6ce7300cd0f6eff14d43273d5064c06009d46076
IMAGE=${PX4_INDI_IMAGE:-px4-indi-sim}
# inputs pinned at the first start (with the binary): a change mid-campaign would mix set-ups, so the chain halts
FROZEN_INPUTS=(
	"$PARAMS"
	indi_flight/bench/g3_run.py indi_flight/bench/g3_sample.py indi_flight/bench/run_scenario.py
	indi_flight/bench/scenarios.py indi_flight/bench/scenario_overrides.py indi_flight/bench/disturbance.py
	indi_flight/bench/model_variant.py indi_flight/bench/run_validity.py indi_flight/bench/provenance.py
	indi_flight/bench/metrics.py indi_flight/bench/stick_pilot.py indi_flight/bench/stick_profile.py
	indi_flight/bench/params/quad5in_indi_g1.params indi_flight/sim/models/quad5in/model.sdf
	indi_flight/sim/worlds/default.sdf
	indi_flight/bench/g3_score.sh indi_flight/bench/g3_checks.py indi_flight/bench/g3_checks_key2.py
)

MAX_CONSECUTIVE_BAD=3 # circuit breaker: failed (after retry) or void indices in a row
MIN_FREE_GB=5
CONTAINER_PREFIX=g3c_ # containers px4-indi-g3c_NNN (flight), px4-indi-g3c_k1 / g3c_k2 (scoring)

ts() { date '+%F %T'; }
die() {
	echo "g3_chain: $*" >&2
	exit 1
}

# ---------------------------------------------------------------------------------------------------------------
# arguments and directory
# ---------------------------------------------------------------------------------------------------------------
resolve_dir() { # $1 = DIR (any cwd-relative or absolute) -> DREL (repo-relative), D (absolute)
	local abs
	abs=$(cd "$OLDCWD" && realpath -m -- "$1") || die "bad directory $1"
	case "$abs" in
	"$REPO"/indi_flight/results/?*) ;;
	*) die "DIR must be under $REPO/indi_flight/results (got $abs)" ;;
	esac
	D=$abs
	DREL=${abs#"$REPO"/}
}

default_dir() { # absolute
	if [ -s "$DIRFILE" ]; then echo "$REPO/$(cat "$DIRFILE")"; else echo "$REPO/$DEFAULT_DIR"; fi
}

lock_held() { # 0 if a chain (or a rescore) holds the lock
	[ -f "$LOCK" ] || return 1
	! flock -n "$LOCK" true 9>&-
}

runname() { printf 'run_%03d' "$1"; }

# ---------------------------------------------------------------------------------------------------------------
# status (python: JSON is read and written atomically)
# ---------------------------------------------------------------------------------------------------------------
# write_status STATE [CURRENT_IDX] [PHASE]; counts are recomputed from the run directories
write_status() {
	python3 - "$D" "$1" "${2:-}" "${3:-}" "${CHAIN_PID:-}" "${RANGE_A:-}" "${RANGE_B:-}" "${STARTED:-}" 8>&- <<'PY'
import json, os, re, sys, time
d, state, cur, phase, pid, a, b, started = sys.argv[1:9]
path = os.path.join(d, "chain_status.json")
try:
    st = json.load(open(path))
except (OSError, ValueError):
    st = {}
a = int(a) if a else st.get("idx_first", 0)
b = int(b) if b else st.get("idx_last", 299)
done = failed = pending_score = k1 = k2 = scored = 0
outcomes = {}
for i in range(a, b + 1):
    r = os.path.join(d, f"run_{i:03d}")
    if os.path.exists(os.path.join(r, "g3_done.json")):
        done += 1
        try:
            o = json.load(open(os.path.join(r, "g3_done.json"))).get("outcome", "?")
        except ValueError:
            o = "?"
        outcomes[o] = outcomes.get(o, 0) + 1
        try:
            s = json.load(open(os.path.join(r, "chain_score.json")))
            scored += 1
            k1 += s["key1"] == "pass"
            k2 += s["key2"] == "pass"
        except (OSError, ValueError, KeyError):
            pending_score += 1
    elif os.path.exists(os.path.join(r, "CHAIN_FAILED")):
        failed += 1
remaining = (b - a + 1) - done - failed
cycles = []
try:
    for line in open(os.path.join(d, "progress.txt")):
        m = re.search(r" cycle=(\d+)s", line)
        if m:
            cycles.append(int(m.group(1)))
except OSError:
    pass
mean = sum(cycles[-20:]) / len(cycles[-20:]) if cycles else 140.0
now = time.time()
st.update({
    "state": state, "pid": int(pid) if pid else st.get("pid"), "current_idx": int(cur) if cur else None,
    "phase": phase or None, "idx_first": a, "idx_last": b, "done": done, "failed": failed, "remaining": remaining,
    "outcomes": outcomes, "scored": scored, "score_pending": pending_score, "key1_pass": k1, "key2_pass": k2,
    "binary_sha256": open(os.path.join(d, "chain_freeze.sha256")).read().split()[0]
    if os.path.exists(os.path.join(d, "chain_freeze.sha256")) else None,
    "started": started or st.get("started"), "updated": time.strftime("%F %T"),
    "mean_cycle_s": round(mean, 1),
    "speed": float(open(os.path.join(d, "chain_speed")).read()) if os.path.exists(os.path.join(d, "chain_speed")) else None,
    "eta": time.strftime("%F %T", time.localtime(now + remaining * mean)) if state == "running" else None,
})
tmp = path + ".tmp"
with open(tmp, "w") as fh:
    json.dump(st, fh, indent=1)
    fh.write("\n")
os.replace(tmp, path)
PY
}

print_status() {
	local held=no
	lock_held && held=yes
	python3 - "$D" "$held" <<'PY'
import json, os, sys
d, held = sys.argv[1:3]
p = os.path.join(d, "chain_status.json")
if not os.path.exists(p):
    print(f"no chain status in {d} (lock held: {held})")
    sys.exit(0)
s = json.load(open(p))
alive = False
if s.get("pid"):
    try:
        os.kill(s["pid"], 0)
        alive = True
    except OSError:
        pass
state = s["state"]
if state == "running" and held == "no":
    state = "DEAD (status says running, lock not held: chain died; restart with start)"
print(f"G3 chain {d}: {state}; pid {s.get('pid')} {'alive' if alive else 'not running'}; lock held: {held}")
print(f"  range {s['idx_first']}-{s['idx_last']}: done {s['done']} {s.get('outcomes', {})}, failed {s['failed']}, "
      f"remaining {s['remaining']}; current idx {s.get('current_idx')} {s.get('phase') or ''}")
print(f"  scored {s['scored']} (pending {s['score_pending']}): key 1 pass {s['key1_pass']}, key 2 pass {s['key2_pass']}")
print(f"  binary {str(s.get('binary_sha256'))[:12]}..., started {s.get('started')}, updated {s.get('updated')}, "
      f"speed {s.get('speed')}, mean cycle {s.get('mean_cycle_s')} s, ETA {s.get('eta')}")
for f in ("CHAIN_HALTED", "CHAIN_FINISHED", "STOP_CHAIN"):
    if os.path.exists(os.path.join(d, f)):
        first = (open(os.path.join(d, f)).readline().strip() or "(empty)")
        print(f"  {f}: {first}")
PY
}

progress() { echo "$(ts) $*" >>"$D/progress.txt"; }

# ---------------------------------------------------------------------------------------------------------------
# freeze guard
# ---------------------------------------------------------------------------------------------------------------
binary_sha() { sha256sum "$BINARY" 2>/dev/null | cut -d' ' -f1; }
image_id() { docker image inspect "$IMAGE" -f '{{.Id}}' 2>/dev/null; }

# 0 if the binary, the frozen inputs and the image still match the pins of DIR; reason on stdout otherwise
freeze_ok() {
	local bad img
	bad=$(sha256sum -c --quiet "$D/chain_freeze.sha256" 2>&1 | head -5)
	[ -z "$bad" ] || {
		echo "frozen input changed: $bad" | tr '\n' ' '
		return 1
	}
	img=$(image_id)
	[ "$img" = "$(cat "$D/chain_image_id")" ] || {
		echo "docker image $IMAGE is now ${img:-missing}, pinned $(cat "$D/chain_image_id")"
		return 1
	}
}

pin_freeze() { # first start in DIR only: binary (verified by the caller), inputs, image
	{
		sha256sum "$BINARY"
		sha256sum "${FROZEN_INPUTS[@]}"
	} >"$D/chain_freeze.sha256" || die "cannot hash the frozen inputs"
	image_id >"$D/chain_image_id"
	[ -s "$D/chain_image_id" ] || die "docker image $IMAGE not found"
}

# ---------------------------------------------------------------------------------------------------------------
# chain body (runs detached, holds the lock on fd 8; children get 8>&- so the lock dies with the chain)
# ---------------------------------------------------------------------------------------------------------------
CUR_PID=
CUR_CONTAINER=
STOP_NOW=0

kill_current() {
	if [ -n "$CUR_CONTAINER" ]; then
		docker stop -t 10 "$CUR_CONTAINER" >/dev/null 2>&1
	fi
	if [ -n "$CUR_PID" ] && kill -0 "$CUR_PID" 2>/dev/null; then
		kill -TERM "$CUR_PID" 2>/dev/null
	fi
}

on_signal() {
	STOP_NOW=1
	kill_current
}

# remove leftover chain containers (a chain killed with -9 leaves its flight container running)
kill_orphans() {
	local ids
	ids=$(docker ps -aq --filter "name=^px4-indi-${CONTAINER_PREFIX}" 2>/dev/null)
	[ -z "$ids" ] && return
	progress "removing leftover containers: $(docker ps -a --filter "name=^px4-indi-${CONTAINER_PREFIX}" --format '{{.Names}}' | paste -sd' ')"
	# shellcheck disable=SC2086
	docker rm -f $ids >/dev/null 2>&1
}

# run_bg CONTAINER_NAME OUTFILE CMD...: run in the background so a signal can interrupt it; sets RC
run_bg() {
	local name=$1 out=$2
	shift 2
	if [ "$STOP_NOW" = 1 ]; then # signal arrived outside a background wait: start nothing new
		RC=143
		return
	fi
	CUR_CONTAINER=px4-indi-$name
	docker rm -f "$CUR_CONTAINER" >/dev/null 2>&1
	"$@" >"$out" 2>&1 </dev/null 8>&- &
	CUR_PID=$!
	wait "$CUR_PID"
	RC=$?
	while kill -0 "$CUR_PID" 2>/dev/null; do # wait was interrupted by a trapped signal
		wait "$CUR_PID"
		RC=$?
	done
	CUR_PID=
	CUR_CONTAINER=
}

halt() { # halt REASON...: write CHAIN_HALTED, state halted, exit
	{
		echo "$(ts) HALTED: $*"
		echo "The chain stopped itself; remaining runs are not flown. Diagnose the reason above (progress.txt,"
		echo "chain.log, stream_NNN.txt), fix it, then rm CHAIN_HALTED and restart: bash indi_flight/bench/g3_chain.sh start $DREL"
	} >"$D/CHAIN_HALTED"
	progress "HALT $*"
	write_status halted
	exit 2
}

fly() { # fly IDX ATTEMPT -> sets RESULT (ok|aborted|void|failed|interrupted), RC, DUR
	local idx=$1 attempt=$2 r d t0
	r=$(runname "$idx")
	d=$D/$r
	if [ -e "$d" ]; then # partial run of a killed or failed flight: keep it aside, fly into a clean directory
		mkdir -p "$D/partial"
		mv "$d" "$D/partial/$r.$(date +%Y%m%d-%H%M%S)" || halt "cannot move partial $d aside"
	fi
	t0=$(date +%s)
	if [ -n "${G3_CHAIN_TEST_FLIGHT_CMD:-}" ]; then # TEST HOOK, see header
		run_bg "${CONTAINER_PREFIX}${idx}" "$D/stream_$idx.txt" bash -c "$G3_CHAIN_TEST_FLIGHT_CMD"
	else
		run_bg "${CONTAINER_PREFIX}$(printf %03d "$idx")" "$D/stream_$idx.txt" \
			timeout "$FLIGHT_TIMEOUT_S" indi_project/docker/run.sh -n "${CONTAINER_PREFIX}$(printf %03d "$idx")" -t "$CONTAINER_TIMEOUT_S" -- \
			python3 indi_flight/bench/g3_run.py --seed "$SEED" --n "$N" --start "$idx" --stop "$idx" \
			--base-params "$PARAMS" --out-root "$DREL" --timeout-s "$RUN_TIMEOUT_S" --speed "$SPEED"
	fi
	DUR=$(($(date +%s) - t0))
	if [ "$STOP_NOW" = 1 ]; then
		RESULT=interrupted
	elif [ -f "$d/g3_done.json" ]; then # g3_run finished the run: ok, aborted (flight failure) or void (invalid)
		RESULT=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("outcome", "unknown"))' "$d/g3_done.json" 2>/dev/null)
		[ -n "$RESULT" ] || RESULT=unknown
	else
		RESULT=failed # rc != 0, timeout (rc 124) or g3_run "incomplete" (g3_failed.json, rc 0)
	fi
	progress "idx=$idx attempt=$attempt rc=$RC dur=${DUR}s result=$RESULT"
}

# score IDX: key 1 (g3_score.sh on a one-run directory) and key 2 (g3_checks_key2.py), args as score_all.sh
score() {
	local idx=$1 r d tmp args
	r=$(runname "$idx")
	d=$D/$r
	rm -f "$d/chain_score.json" "$d/SCORE_PENDING" "$d/g3_checks.json" "$d/g3_checks.txt"
	write_status "${STATUS_STATE:-running}" "$idx" scoring
	# g3_score.sh scores every run_* of a directory: give it a directory holding only a link to this run
	tmp=$D/.score_tmp
	rm -rf "$tmp"
	mkdir -p "$tmp" && ln -s "../$r" "$tmp/$r"
	run_bg "${CONTAINER_PREFIX}k1" "$d/chain_key1.txt" \
		timeout 1000 indi_project/docker/run.sh -n "${CONTAINER_PREFIX}k1" -t 900 -- bash indi_flight/bench/g3_score.sh "$DREL/.score_tmp"
	rm -rf "$tmp"
	[ "$STOP_NOW" = 1 ] && {
		echo "interrupted by stop --now" >"$d/SCORE_PENDING"
		return
	}
	args=$(grep -E "^$r --t0 " "$d/chain_key1.txt" | head -1 | cut -d' ' -f2-)
	mkdir -p "$D/key2"
	rm -f "$D/key2/$r.json"
	if [ -n "$args" ]; then
		# shellcheck disable=SC2086 # args is the flag list printed by g3_score.sh
		run_bg "${CONTAINER_PREFIX}k2" "$d/chain_key2.txt" \
			timeout 600 indi_project/docker/run.sh -n "${CONTAINER_PREFIX}k2" -t 500 -- \
			python3 indi_flight/bench/g3_checks_key2.py "$DREL/$r" $args --out "$DREL/key2"
	else
		echo "no key-1 argument line for $r (see chain_key1.txt): key 2 not run" >"$d/chain_key2.txt"
	fi
	[ "$STOP_NOW" = 1 ] && {
		echo "interrupted by stop --now" >"$d/SCORE_PENDING"
		return
	}
	python3 - "$D" "$idx" "$args" 8>&- <<'PY'
import json, os, sys, time
d, idx, args = sys.argv[1], int(sys.argv[2]), sys.argv[3]
r = f"run_{idx:03d}"
rd = os.path.join(d, r)
outcome = json.load(open(os.path.join(rd, "g3_done.json"))).get("outcome")
missing = []
try:
    k1 = json.load(open(os.path.join(rd, "g3_checks.json")))
except (OSError, ValueError):
    k1 = None
    missing.append("key 1 g3_checks.json (see chain_key1.txt)")
try:
    k2 = json.load(open(os.path.join(d, "key2", r + ".json")))
except (OSError, ValueError):
    k2 = None
    missing.append("key 2 key2/%s.json (see chain_key2.txt)" % r)
if missing:
    open(os.path.join(rd, "SCORE_PENDING"), "w").write("missing: " + "; ".join(missing) + "\n")
    sys.exit(0)
items = ("item1_loc", "item2_oscillation", "item3_steady_state")
fail = lambda j: [k.split("_")[0] for k in items if not j.get(k, {}).get("pass")]
s = {"idx": idx, "outcome": outcome, "key1": "pass" if k1.get("pass") else "FAIL", "key1_failing": fail(k1),
     "key2": "pass" if k2.get("pass") else "FAIL", "key2_failing": fail(k2),
     "key2_col5_g4_chatter_pass": k2.get("chatter", {}).get("pass"), "score_args": args,
     "scored": time.strftime("%F %T")}
json.dump(s, open(os.path.join(rd, "chain_score.json"), "w"), indent=1)
PY
	if [ -f "$d/SCORE_PENDING" ]; then
		progress "idx=$idx score=PENDING $(head -c 200 "$d/SCORE_PENDING")"
	else
		progress "idx=$idx score key1=$(jq -r .key1 "$d/chain_score.json" 2>/dev/null) key2=$(jq -r .key2 "$d/chain_score.json" 2>/dev/null)"
	fi
	scores_tsv
}

scores_tsv() { # SCORES.tsv rebuilt from the per-run chain_score.json / SCORE_PENDING
	python3 - "$D" 8>&- <<'PY'
import glob, json, os, sys
d = sys.argv[1]
rows = ["idx\toutcome\tkey1\tkey2\tkey1_failing\tkey2_failing\tkey2_col5_g4_chatter(not G3)"]
for rd in sorted(glob.glob(os.path.join(d, "run_[0-9][0-9][0-9]"))):
    idx = rd[-3:]
    try:
        o = json.load(open(os.path.join(rd, "g3_done.json"))).get("outcome")
    except (OSError, ValueError):
        continue
    try:
        s = json.load(open(os.path.join(rd, "chain_score.json")))
        rows.append("\t".join([idx, o, s["key1"], s["key2"], ",".join(s["key1_failing"]) or "-",
                               ",".join(s["key2_failing"]) or "-", str(s["key2_col5_g4_chatter_pass"])]))
    except (OSError, ValueError, KeyError):
        rows.append("\t".join([idx, o, "UNSCORED", "UNSCORED", "-", "-", "-"]))
tmp = os.path.join(d, "SCORES.tsv.tmp")
open(tmp, "w").write("\n".join(rows) + "\n")
os.replace(tmp, os.path.join(d, "SCORES.tsv"))
PY
}

close_inherited_fds() { # everything above stderr except the file bash reads this script from
	local fd p
	for p in "/proc/$$/fd"/*; do
		fd=${p##*/}
		[ "$fd" -gt 2 ] 2>/dev/null || continue
		[ "$(readlink "$p" 2>/dev/null)" = "$SELF" ] && continue
		eval "exec $fd>&-" 2>/dev/null
	done
}

run_chain() {
	close_inherited_fds
	exec 8>>"$LOCK"
	flock -w 10 8 || {
		echo "$(ts) lock busy, another chain runs: exit"
		exit 1
	}
	echo "$DREL" >"$DIRFILE"
	CHAIN_PID=$$
	STARTED=$(ts)
	trap on_signal TERM INT
	echo "$(ts) chain pid $$ sid $(ps -o sid= -p $$ | tr -d ' ') range $RANGE_A-$RANGE_B dir $DREL"
	kill_orphans
	progress "START pid=$$ range=$RANGE_A-$RANGE_B speed=$SPEED binary=$(head -1 "$D/chain_freeze.sha256" | cut -c1-12)${G3_CHAIN_TEST_FLIGHT_CMD:+ TEST_FLIGHT_CMD=$G3_CHAIN_TEST_FLIGHT_CMD}"
	write_status running
	local idx r d bad=0 streak=() c0 avail reason pinned got
	pinned=$(cut -d' ' -f1 "$D/chain_freeze.sha256" | head -1)
	for idx in $(seq "$RANGE_A" "$RANGE_B"); do
		r=$(runname "$idx")
		d=$D/$r
		if [ -f "$D/STOP_CHAIN" ] || [ "$STOP_NOW" = 1 ]; then break; fi
		[ -f "$d/g3_done.json" ] && continue
		[ -f "$d/CHAIN_FAILED" ] && continue
		# before each flight: freeze and host
		reason=$(freeze_ok) || halt "$reason"
		avail=$(df -BG --output=avail "$D" | tail -1 | tr -dc 0-9)
		[ "${avail:-0}" -ge "$MIN_FREE_GB" ] || halt "free disk ${avail} GB < $MIN_FREE_GB GB"
		c0=$(date +%s)
		write_status running "$idx" flying
		fly "$idx" 1
		if [ "$RESULT" = failed ]; then
			if [ -f "$D/STOP_CHAIN" ]; then
				RESULT=interrupted # stop requested: no retry, the index stays unmarked and is flown on the next start
			else
				fly "$idx" 2
			fi
		fi
		if [ "$RESULT" = interrupted ]; then
			progress "idx=$idx INTERRUPTED (stop requested); flown again on the next start"
			break
		fi
		if [ "$RESULT" = failed ]; then
			mkdir -p "$d"
			echo "$(ts) failed twice (last rc $RC, see progress.txt, stream_$idx.txt)" >"$d/CHAIN_FAILED"
			bad=$((bad + 1))
			streak+=("$idx")
		else
			# freeze guard on the flown run: the binary the runner recorded
			got=$(jq -r '.provenance.binary_sha256 // empty' "$d/run.json" 2>/dev/null)
			[ -z "$got" ] || [ "$got" = "$pinned" ] || halt "$r flew binary ${got:0:12}, pinned ${pinned:0:12} (firmware rebuilt mid-campaign)"
			[ -n "$got" ] || progress "idx=$idx WARNING no provenance.binary_sha256 in run.json"
			if [ "$RESULT" = void ]; then # validity failed: wrong controller/params, a set-up fault more than a result
				bad=$((bad + 1))
				streak+=("$idx")
			else
				bad=0
				streak=()
			fi
			score "$idx"
			[ "$STOP_NOW" = 1 ] && break
		fi
		progress "idx=$idx cycle=$(($(date +%s) - c0))s"
		write_status running "$idx" flown
		if [ "$bad" -ge "$MAX_CONSECUTIVE_BAD" ]; then
			# most likely docker/host trouble: unmark the streak so a restart re-flies it
			for i in "${streak[@]}"; do rm -f "$D/$(runname "$i")/CHAIN_FAILED"; done
			halt "$bad consecutive failed or void indices (${streak[*]}): host/docker/set-up trouble suspected, not a controller result; CHAIN_FAILED markers of these indices removed so a restart re-flies them"
		fi
	done
	if [ "$STOP_NOW" = 1 ] || [ -f "$D/STOP_CHAIN" ]; then
		progress "STOPPED ($([ "$STOP_NOW" = 1 ] && echo now || echo after the current run))"
		rm -f "$D/STOP_CHAIN"
		write_status stopped
		exit 0
	fi
	local left
	left=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["remaining"])' "$D/chain_status.json" 2>/dev/null)
	scores_tsv
	if [ "${left:-1}" = 0 ]; then
		echo "$(ts) all indices $RANGE_A-$RANGE_B have g3_done.json or CHAIN_FAILED; see SCORES.tsv" >"$D/CHAIN_FINISHED"
		progress "FINISHED range=$RANGE_A-$RANGE_B"
		write_status finished
	else
		progress "END of pass with $left remaining"
		write_status stopped
	fi
	exit 0
}

# ---------------------------------------------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------------------------------------------
cmd_start() {
	local allow="" pos=() a speed=""
	while [ $# -gt 0 ]; do
		case "$1" in
		--allow-binary)
			allow=${2:-}
			[ -n "$allow" ] || die "--allow-binary needs a SHA-256"
			shift 2
			;;
		--speed)
			speed=${2:-}
			if ! [[ "$speed" =~ ^[0-9]+(\.[0-9]+)?$ ]] || ! awk "BEGIN { exit !($speed > 0) }"; then
				die "--speed needs a positive number"
			fi
			shift 2
			;;
		-*) die "unknown option $1" ;;
		*)
			pos+=("$1")
			shift
			;;
		esac
	done
	case ${#pos[@]} in
	0) resolve_dir "$REPO/$DEFAULT_DIR" ;;
	1 | 3) resolve_dir "${pos[0]}" ;;
	2) die "give DIR before the range: start DIR IDX_FIRST IDX_LAST" ;;
	*) die "too many arguments" ;;
	esac
	if [ ${#pos[@]} -eq 3 ]; then
		RANGE_A=${pos[1]} RANGE_B=${pos[2]}
	elif [ -s "$D/chain_range" ]; then
		read -r RANGE_A RANGE_B <"$D/chain_range"
	else
		RANGE_A=0 RANGE_B=$((N - 1))
	fi
	for a in "$RANGE_A" "$RANGE_B"; do [[ "$a" =~ ^[0-9]+$ ]] || die "bad index $a"; done
	if [ "$RANGE_A" -gt "$RANGE_B" ] || [ "$RANGE_B" -ge "$N" ]; then die "range must satisfy 0 <= first <= last < $N"; fi

	if lock_held; then
		echo "g3_chain: refused, a chain (or rescore) already holds $LOCK" >&2
		D_SAVE=$D
		resolve_dir "$(default_dir)"
		print_status
		D=$D_SAVE
		exit 1
	fi
	if [ -n "${G3_CHAIN_TEST_FLIGHT_CMD:-}" ]; then
		case "$(basename "$D")" in *smoke*) ;; *) die "G3_CHAIN_TEST_FLIGHT_CMD is a test hook, refused outside a *smoke* directory" ;; esac
	fi
	[ -f "$D/CHAIN_HALTED" ] && {
		cat "$D/CHAIN_HALTED" >&2
		die "refused: $DREL/CHAIN_HALTED exists (diagnose, then rm it)"
	}
	[ -f "$D/CHAIN_FINISHED" ] && die "refused: $DREL/CHAIN_FINISHED exists, nothing to fly"
	command -v docker >/dev/null || die "docker not found"
	[ -n "$(image_id)" ] || die "docker image $IMAGE not found"

	# freeze: the binary must be the FREEZE-10 gate binary (or the explicit override), and match the pins of DIR
	local cur
	cur=$(binary_sha)
	[ -n "$cur" ] || die "$BINARY missing"
	if [ -f "$D/chain_freeze.sha256" ]; then
		local pinned
		pinned=$(cut -d' ' -f1 "$D/chain_freeze.sha256" | head -1)
		[ -z "$allow" ] || [ "$allow" = "$pinned" ] || die "refused: --allow-binary ${allow:0:12} differs from the binary pinned in $DREL (${pinned:0:12}); one campaign, one binary"
		local reason
		reason=$(freeze_ok) || die "refused: $reason"
	else
		local want=${allow:-$FREEZE_BINARY_SHA}
		[ "$cur" = "$want" ] || die "refused: $BINARY sha256 $cur is not the expected ${want} (FREEZE-10 gate binary unless --allow-binary)"
		mkdir -p "$D" || die "cannot create $D"
		pin_freeze
	fi
	mkdir -p "$D" "$(dirname "$LOCK")"
	# speed factor: pinned at the first start, a campaign does not mix speeds
	if [ -s "$D/chain_speed" ]; then
		[ -z "$speed" ] || awk "BEGIN { exit !($speed == $(cat "$D/chain_speed")) }" || die "refused: --speed $speed differs from the speed pinned in $DREL ($(cat "$D/chain_speed"))"
	else
		awk "BEGIN { printf \"%.6g\n\", ${speed:-1.0} }" >"$D/chain_speed"
	fi
	echo "$RANGE_A $RANGE_B" >"$D/chain_range"
	[ -f "$D/.gitignore" ] || printf '# chain scratch: partial runs of killed flights, scoring link directory\npartial/\n.score_tmp/\n*.tmp\n' >"$D/.gitignore"
	rm -f "$D/STOP_CHAIN"

	local inhibit=()
	command -v systemd-inhibit >/dev/null && inhibit=(systemd-inhibit --what=sleep:idle:handle-lid-switch
		--who="indi G3 flight chain" --why="G3 campaign flights running" --mode=block)
	# new session, no terminal, stdin /dev/null, the supervisor's lock fd 9 closed; survives the caller's exit
	RANGE_A=$RANGE_A RANGE_B=$RANGE_B setsid nohup "${inhibit[@]}" bash "$SELF" _run "$DREL" \
		</dev/null >>"$D/chain.log" 2>&1 9>&- &
	local i launched
	launched=$(ts)
	for i in $(seq 1 30); do
		sleep 1
		lock_held && [ -f "$D/chain_status.json" ] && break
	done
	sleep 1
	if lock_held; then
		echo "g3_chain: started (log $DREL/chain.log)"
		print_status
	elif [[ "$(jq -r '.started // ""' "$D/chain_status.json" 2>/dev/null)" > "$launched" ]] ||
		[ "$(jq -r '.started // ""' "$D/chain_status.json" 2>/dev/null)" = "$launched" ]; then
		echo "g3_chain: the chain started and has already ended:"
		print_status
		[ ! -f "$D/CHAIN_HALTED" ]
		exit
	else
		echo "g3_chain: the chain did not take the lock; tail of $DREL/chain.log:" >&2
		tail -5 "$D/chain.log" >&2
		exit 1
	fi
}

cmd_stop() {
	local now=0 pos=() pid
	for a in "$@"; do
		case "$a" in
		--now) now=1 ;;
		-*) die "unknown option $a" ;;
		*) pos+=("$a") ;;
		esac
	done
	resolve_dir "${pos[0]:-$(default_dir)}"
	[ -d "$D" ] || die "$D does not exist"
	echo "$(ts) stop requested$([ $now = 1 ] && echo ' (now)')" >"$D/STOP_CHAIN"
	pid=$(jq -r '.pid // empty' "$D/chain_status.json" 2>/dev/null)
	if [ "$now" = 1 ]; then
		if lock_held && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
			kill -TERM "$pid"
		fi
		# chain already dead (kill -9): its flight container may still run
		lock_held || docker ps -q --filter "name=^px4-indi-${CONTAINER_PREFIX}" | xargs -r docker stop -t 10 >/dev/null
	fi
	if ! lock_held; then
		rm -f "$D/STOP_CHAIN"
		echo "g3_chain: no chain running"
		print_status
		return
	fi
	if [ "$now" = 0 ]; then
		echo "g3_chain: STOP_CHAIN written; the chain stops after the current run (and its scoring)"
		return
	fi
	local i
	for i in $(seq 1 60); do
		lock_held || break
		sleep 1
	done
	lock_held && die "chain still holds the lock after 60 s"
	echo "g3_chain: stopped"
	print_status
}

cmd_status() {
	resolve_dir "${1:-$(default_dir)}"
	print_status
}

cmd_rescore() {
	resolve_dir "${1:-$(default_dir)}"
	[ -d "$D" ] || die "$D does not exist"
	exec 8>>"$LOCK"
	flock -n 8 || die "refused: the lock is held (chain flying or another rescore); stop the chain first"
	trap on_signal TERM INT
	local d idx n=0 state
	state=$(jq -r '.state // "stopped"' "$D/chain_status.json" 2>/dev/null)
	STATUS_STATE=$state
	for d in "$D"/run_[0-9][0-9][0-9]; do
		[ -f "$d/g3_done.json" ] || continue
		[ -f "$d/chain_score.json" ] && [ ! -f "$d/SCORE_PENDING" ] && continue
		idx=$((10#${d##*_}))
		echo "rescoring $(basename "$d")"
		score "$idx"
		n=$((n + 1))
		[ "$STOP_NOW" = 1 ] && break
	done
	scores_tsv
	write_status "$state"
	exec 8>&-
	echo "g3_chain: rescored $n run(s)"
	print_status
}

OLDCWD=${G3_CHAIN_CALLER_CWD:-$OLDPWD}
[ -n "$OLDCWD" ] || OLDCWD=$REPO
case "${1:-}" in
start)
	shift
	cmd_start "$@"
	;;
stop)
	shift
	cmd_stop "$@"
	;;
status)
	shift
	cmd_status "$@"
	;;
rescore)
	shift
	cmd_rescore "$@"
	;;
_run) # internal: the detached chain
	resolve_dir "$2"
	SPEED=$(cat "$D/chain_speed")
	run_chain
	;;
*)
	sed -n '2,15p' "$SELF" | sed 's/^# \{0,1\}//'
	exit 64
	;;
esac
