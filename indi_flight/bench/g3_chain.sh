#!/usr/bin/env bash
# Detached, resumable, serial flight chain for the G3 campaign (seed 173, n 300, FREEZE-10).
#
#   bash indi_flight/bench/g3_chain.sh start   [DIR] [IDX_FIRST IDX_LAST] [--allow-binary SHA256] [--speed F]
#                                              [--samples SAMPLE_DIR] [--halt-on-fail]
#   bash indi_flight/bench/g3_chain.sh status  [DIR]
#   bash indi_flight/bench/g3_chain.sh stop    [DIR] [--now]
#   bash indi_flight/bench/g3_chain.sh rescore [DIR]
#
# DIR (default indi_flight/results/g3_campaign_f10) must be under indi_flight/results. The range of the first start in
# DIR (default 0 299) is the campaign range: CHAIN_FINISHED means all of it is finished. A later start may fly a
# sub-range of it. --speed F: sim speed factor (g3_run.py --speed), default 1.0, pinned per DIR.
# One flight at a time, in index order; a finished run (run_NNN/g3_done.json, flight result) is checked and skipped.
# The chain holds indi_flight/logs/flight_chain.lock while it runs: a held lock means "gate flights in progress".
# It ignores indi_flight/STOP (the supervisor's stop file): the chain flies across supervisor stops.
# Per run, same command as results/g3_pretest_q24_s197/fly_all.sh, then both scoring keys as in score_all.sh.
# --samples SAMPLE_DIR (S212 re-fly, first start only, pinned in DIR/chain_samples and in the freeze hashes): the draws come
# from SAMPLE_DIR (g3_sample.py refly: run_NNN.json + index.json, with the S211 `actc` block) instead of the seed's
# campaign; g3_run.py is called with --samples and --require-actc. Without it the campaign is unchanged.
# --halt-on-fail (pinned in DIR/chain_halt_on_fail): after both keys score a run, the chain halts (CHAIN_HALTED, state
# halted, HALT_ON_FAIL.json) when item 1 or item 2 is FAIL on BOTH keys. Resume: rm CHAIN_HALTED HALT_ON_FAIL.json, start.
# No git, no Claude. See results/g3_campaign_f10/README.md.
#
# TEST HOOK (smoke tests only): G3_CHAIN_TEST_FLIGHT_CMD="false" replaces the flight command by that shell command;
# G3_CHAIN_TEST_SCORE_CMD replaces the docker scoring (env OUT=run dir, IDX; it writes chain_score.json itself).
# Both are refused unless DIR's name contains "smoke". Only the campaign DIR is recorded in logs/flight_chain.dir.
set -u
export LC_NUMERIC=C

REPO=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd) || exit 1
cd "$REPO" || exit 1
SELF=$REPO/indi_flight/bench/g3_chain.sh
LOCK=$REPO/indi_flight/logs/flight_chain.lock
DIRFILE=$REPO/indi_flight/logs/flight_chain.dir # repo-relative DIR, written only for the campaign DEFAULT_DIR
DEFAULT_DIR=indi_flight/results/g3_campaign_f10

# campaign definition (results/g3_pretest_q24_s197/fly_all.sh)
SEED=173
N=300
PARAMS_DEFAULT=indi_flight/results/g5_freeze_s157/params.params
PARAMS=${G3_PARAMS:-$PARAMS_DEFAULT} # repo-relative; G3_PARAMS overrides at the first start of a DIR, then pinned in DIR/chain_params
FLIGHT_TIMEOUT_S=1700 # host timeout around run.sh
CONTAINER_TIMEOUT_S=1500
RUN_TIMEOUT_S=1200 # g3_run.py --timeout-s
BUILD=build/px4_sitl_default
BINARY=$BUILD/bin/px4
# FREEZE-10 gate binary: provenance.binary_sha256 of every run in results/g3_pretest_q24_s197/run_*/run.json
FREEZE_BINARY_SHA=d220e19315c2798aa18a1bab6ce7300cd0f6eff14d43273d5064c06009d46076
IMAGE=${PX4_INDI_IMAGE:-px4-indi-sim}
# inputs pinned at the first start (with the binary): a change mid-campaign would mix set-ups, so the chain halts
FROZEN_INPUTS=(
	"$PARAMS"
	indi_flight/bench/g3_run.py indi_flight/bench/g3_sample.py indi_flight/bench/run_scenario.py
	indi_flight/bench/scenarios.py indi_flight/bench/scenario_overrides.py indi_flight/bench/disturbance.py
	indi_flight/bench/model_variant.py indi_flight/bench/run_validity.py indi_flight/bench/provenance.py
	indi_flight/bench/metrics.py indi_flight/bench/g4_metrics.py indi_flight/bench/stick_pilot.py
	indi_flight/bench/stick_profile.py indi_flight/bench/params/quad5in_indi_g1.params
	indi_flight/sim/models/quad5in/model.sdf indi_flight/sim/models/quad5in/model.config
	indi_flight/sim/worlds/default.sdf
	indi_flight/bench/g3_score.sh indi_flight/bench/g3_checks.py indi_flight/bench/g3_checks_key2.py
	"$BUILD/gz_env.sh" "$BUILD/parameters.xml" src/modules/simulation/gz_bridge/server.config
)
# plus every file of $BUILD/etc (PX4 start-up scripts and airframes) and the gz plugins (frozen_build_files)

# A g3_run "aborted" run (run.json exit_status failed) is a FLIGHT RESULT (kept, counted) unless its error is on the
# INFRA whitelist below (runner/host faults of run_scenario.py before or outside the flight): those are moved to
# partial/ and flown again. Never extend the whitelist to a failure the controller could cause: a failure is excluded
# only by the gate's class (a) with proof on the log, never by the chain.
#   flight watchdog: the O-12 watchdogs (run_scenario.py wd_check), take-off end to land command
FLIGHT_WATCHDOGS='^(non-finite attitude or rate|tilt > [0-9.]+ deg for [0-9.]+ s|height < [0-9.]+ m|> [0-9.]+ m below hold altitude for [0-9.]+ s)$'
#   infra: matched on run.json "error" up to the first " | " (TypeName: message, run_scenario.py main)
INFRA_ERRORS='^(RunError: px4 exited early \(rc=-?[0-9]+\) while waiting for .*|RunError: timeout \([0-9.]+s wall\) waiting for .Startup script returned successfully. in .*|RunError: gz sim exited early|RunError: timeout waiting for gz world|RunError: gz unpause failed:.*|RunError: param (set|show) .* failed:.*|RunError: no MAVLink heartbeat in 60 s|WatchdogTrip: watchdog: no ATTITUDE for [0-9]+ s wall in phase .*)$'
#   host exception types are infra too (OSError and subclasses, subprocess errors, JSONDecodeError), and an abort
#   with no error text but no ulog; any other exception (ValueError, KeyError, ...) is "other": a controller NaN can
#   surface that way in run_scenario.py main() (classify_done)

MAX_CONSECUTIVE_BAD=3   # circuit breaker: failed (infra after retry) or void indices in a row
MAX_CONSECUTIVE_OTHER=10 # aborted-other flight results in a row: kept as results, but the chain stops for a look
DOCKER_TIMEOUT_S=60     # docker CLI calls of the chain itself (stop, rm, ps, inspect)
MIN_FREE_GB=5
CONTAINER_PREFIX=g3c_ # containers px4-indi-g3c_NNN (flight), px4-indi-g3c_k1 / g3c_k2 (scoring)

ts() { date '+%F %T'; }
dk() { timeout "$DOCKER_TIMEOUT_S" docker "$@"; }
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

is_smoke() { case "$(basename "$D")" in *smoke*) return 0 ;; esac; return 1; }

lock_held() { # 0 if a chain (or a rescore) holds the lock
	[ -f "$LOCK" ] || return 1
	! flock -n "$LOCK" true 9>&-
}

runname() { printf 'run_%03d' "$1"; }

read_campaign_range() { read -r CAMP_A CAMP_B <"$D/chain_range"; }

# ---------------------------------------------------------------------------------------------------------------
# status (python: JSON is read and written atomically)
# ---------------------------------------------------------------------------------------------------------------
# write_status STATE [CURRENT_IDX] [PHASE]; counts over the campaign range are recomputed from the run directories
write_status() {
	python3 - "$D" "$1" "${2:-}" "${3:-}" "${CHAIN_PID:-}" "${RANGE_A:-}" "${RANGE_B:-}" "${STARTED:-}" 8>&- <<'PY'
import json, os, re, sys, time
d, state, cur, phase, pid, fa, fb, started = sys.argv[1:9]
path = os.path.join(d, "chain_status.json")
try:
    st = json.load(open(path))
except (OSError, ValueError):
    st = {}
try:
    a, b = (int(x) for x in open(os.path.join(d, "chain_range")).read().split())
except (OSError, ValueError):  # directory from before chain_range existed
    a, b = st.get("idx_first", 0), st.get("idx_last", 299)
fa = int(fa) if fa else st.get("fly_first", a)
fb = int(fb) if fb else st.get("fly_last", b)
done = failed = pending_score = k1 = k2 = scored = left_fly = 0
outcomes = {}
for i in range(a, b + 1):
    r = os.path.join(d, f"run_{i:03d}")
    if os.path.exists(os.path.join(r, "g3_done.json")):
        done += 1
        try:  # chain class (ok, flight, other, void) when the chain has classified the run, else the runner outcome
            o = open(os.path.join(r, "chain_class.txt")).read().split()[0]
        except (OSError, IndexError):
            try:
                o = json.load(open(os.path.join(r, "g3_done.json"))).get("outcome", "?")
            except ValueError:
                o = "?"
        outcomes[o] = outcomes.get(o, 0) + 1
        try:
            s = json.load(open(os.path.join(r, "chain_score.json")))
            if os.path.exists(os.path.join(r, "SCORE_PENDING")):
                raise ValueError
            scored += 1
            k1 += s["key1"] == "pass"
            k2 += s["key2"] == "pass"
        except (OSError, ValueError, KeyError):
            pending_score += 1
    elif os.path.exists(os.path.join(r, "CHAIN_FAILED")):
        failed += 1
    elif fa <= i <= fb:
        left_fly += 1
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
freeze = os.path.join(d, "chain_freeze.sha256")
speed = os.path.join(d, "chain_speed")
st.update({
    "state": state, "pid": int(pid) if pid else st.get("pid"), "current_idx": int(cur) if cur else None,
    "phase": phase or None, "idx_first": a, "idx_last": b,
    "fly_first": fa, "fly_last": fb, "remaining_in_fly_range": left_fly,
    "done": done, "failed": failed, "remaining": remaining,
    "outcomes": outcomes, "scored": scored, "score_pending": pending_score, "key1_pass": k1, "key2_pass": k2,
    "binary_sha256": open(freeze).read().split()[0] if os.path.exists(freeze) else None,
    "params": open(os.path.join(d, "chain_params")).read().strip() if os.path.exists(os.path.join(d, "chain_params")) else None,
    "speed": float(open(speed).read()) if os.path.exists(speed) else None,
    "started": started or st.get("started"), "updated": time.strftime("%F %T"),
    "mean_cycle_s": round(mean, 1),
    "eta": time.strftime("%F %T", time.localtime(time.time() + left_fly * mean)) if state == "running" else None,
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
print(f"  campaign {s['idx_first']}-{s['idx_last']} (flying {s.get('fly_first')}-{s.get('fly_last')}): done {s['done']} "
      f"{s.get('outcomes', {})}, failed {s['failed']}, remaining {s['remaining']}; "
      f"current idx {s.get('current_idx')} {s.get('phase') or ''}")
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
image_id() { dk image inspect "$IMAGE" -f '{{.Id}}' 2>/dev/null; }
frozen_build_files() {
	find "$BUILD/etc" -type f
	find "$BUILD/src/modules/simulation/gz_plugins" -maxdepth 1 -type f -name '*.so'
}

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

pin_freeze() { # first start in DIR only: binary (verified by the caller, first line), inputs, build files, image
	{
		sha256sum "$BINARY"
		sha256sum "${FROZEN_INPUTS[@]}"
		frozen_build_files | sort -u | xargs -d '\n' sha256sum
		[ -z "$SAMPLES" ] || find "$SAMPLES" -type f | sort | xargs -d '\n' sha256sum
	} >"$D/chain_freeze.sha256" || die "cannot hash the frozen inputs"
	image_id >"$D/chain_image_id"
	echo "$PARAMS" >"$D/chain_params"
	[ -z "$SAMPLES" ] || echo "$SAMPLES" >"$D/chain_samples"
	[ -s "$D/chain_image_id" ] || die "docker image $IMAGE not found"
}

# samples dir of DIR (S212 re-fly): repo-relative, pinned in chain_samples at the first start; empty = the seed's own campaign
select_samples() {
	SAMPLES=
	[ -s "$D/chain_samples" ] && SAMPLES=$(cat "$D/chain_samples")
	[ -z "$SAMPLES" ] || [ -f "$REPO/$SAMPLES/index.json" ] || die "samples dir $SAMPLES (pinned in $DREL) has no index.json"
}

# params file of DIR: pinned in chain_params at the first start (DIR without the file = default params file)
select_params() {
	local pinned=$PARAMS_DEFAULT
	[ -s "$D/chain_params" ] && pinned=$(cat "$D/chain_params")
	if [ -f "$D/chain_freeze.sha256" ] || [ -s "$D/chain_params" ]; then
		[ -z "${G3_PARAMS:-}" ] || [ "$G3_PARAMS" = "$pinned" ] || die "refused: G3_PARAMS $G3_PARAMS differs from the params file pinned in $DREL ($pinned)"
		PARAMS=$pinned
	fi
	[ -f "$REPO/$PARAMS" ] || die "params file $PARAMS missing"
	FROZEN_INPUTS[0]=$PARAMS
}

pinned_sha() { head -1 "$D/chain_freeze.sha256" | cut -d' ' -f1; }

# ---------------------------------------------------------------------------------------------------------------
# chain body (runs detached, holds the lock on fd 8; children get 8>&- so the lock dies with the chain)
# ---------------------------------------------------------------------------------------------------------------
CUR_PID=
CUR_CONTAINER=
STOP_NOW=0

kill_current() {
	if [ -n "$CUR_CONTAINER" ]; then
		dk stop -t 10 "$CUR_CONTAINER" >/dev/null 2>&1
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
	ids=$(dk ps -aq --filter "name=^px4-indi-${CONTAINER_PREFIX}" 2>/dev/null)
	[ -z "$ids" ] && return
	progress "removing leftover containers: $(dk ps -a --filter "name=^px4-indi-${CONTAINER_PREFIX}" --format '{{.Names}}' | paste -sd' ')"
	# shellcheck disable=SC2086
	dk rm -f $ids >/dev/null 2>&1
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
	dk rm -f "$CUR_CONTAINER" >/dev/null 2>&1
	"$@" >"$out" 2>&1 </dev/null 8>&- &
	CUR_PID=$!
	[ "$STOP_NOW" = 1 ] && kill_current # signal during the launch (trap ran with CUR_PID empty)
	wait "$CUR_PID"
	RC=$?
	while kill -0 "$CUR_PID" 2>/dev/null; do # wait was interrupted by a trapped signal
		wait "$CUR_PID"
		RC=$?
	done
	CUR_PID=
	CUR_CONTAINER=
}

# move_partial IDX: move run_NNN aside to partial/ (never deleted); prints the new path; non-zero if it fails
# (callers run it in $(...), so they halt: p=$(move_partial I) || halt ...)
move_partial() {
	local r d p
	r=$(runname "$1")
	d=$D/$r
	[ -e "$d" ] || return 0
	mkdir -p "$D/partial" || return 1
	p=$D/partial/$r.$(date +%Y%m%d-%H%M%S)
	[ -e "$p" ] && p=$p.$$.$RANDOM
	mv "$d" "$p" || return 1
	echo "${p#"$D"/}"
}

halt() { # halt REASON...: write CHAIN_HALTED, state halted, exit
	{
		echo "$(ts) HALTED: $*"
		echo "The chain stopped itself; remaining runs are not flown. Diagnose the reason above (progress.txt,"
		echo "chain.log, stream_NNN.txt), fix it, then rm CHAIN_HALTED and restart: bash indi_flight/bench/g3_chain.sh start $DREL"
	} >"$D/CHAIN_HALTED"
	progress "HALT $*"
	scores_tsv
	write_status halted
	exit 2
}

# classify_done FILE -> one line: "ok", "flight watchdog: <reason>", "other <error>" (aborted, kept as a flight
# result), "void <problems>", or "infra <error>" (runner/host fault, flown again)
classify_done() {
	python3 - "$1" "$FLIGHT_WATCHDOGS" "$INFRA_ERRORS" 8>&- <<'PY'
import builtins, json, re, sys
HOST_EXC = {"CalledProcessError", "TimeoutExpired", "SubprocessError", "JSONDecodeError", "gaierror", "herror"}


def host_exception(name):  # OSError family (builtins) or the named subprocess/json/socket errors
    t = getattr(builtins, name, None)
    return name in HOST_EXC or (isinstance(t, type) and issubclass(t, OSError))


try:
    j = json.load(open(sys.argv[1]))
except (OSError, ValueError) as e:
    print(f"infra unreadable g3_done.json ({e})")
    sys.exit(0)
o = j.get("outcome")
one = lambda s: " ".join(str(s).split())[:300]
if o == "ok":
    print("ok")
elif o == "void":
    print("void " + one("; ".join((j.get("validity") or {}).get("problems") or ["validity failed"])))
elif o == "aborted":
    wd = (j.get("watchdog") or {}).get("reason") or ""
    err = j.get("error") or ""
    first = err.split(" | ")[0].strip()
    etype = first.split(":")[0] if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*: ", first) else ""
    if wd and re.match(sys.argv[2], wd):
        print("flight watchdog: " + one(wd))
    elif re.match(sys.argv[3], first):
        print("infra " + one(err))
    elif etype and host_exception(etype):
        print("infra host exception: " + one(err))
    elif not first and "no ulog" in err:
        print("infra no ulog and no error: " + one(err))
    else:
        print("other " + one(err or "aborted, no error text"))
else:
    print(f"infra outcome {o!r}")
PY
}

# check_binary IDX: the run must record the pinned binary; else move it aside and halt
check_binary() {
	local r d got p
	r=$(runname "$1")
	d=$D/$r
	got=$(jq -r '.provenance.binary_sha256 // empty' "$d/run.json" 2>/dev/null)
	[ -n "$got" ] || halt "$r has g3_done.json but no provenance.binary_sha256 in run.json: binary unknown (not moved)"
	if [ "$got" != "$(pinned_sha)" ]; then
		p=$(move_partial "$1") || halt "$r flew binary $got (pinned $(pinned_sha)) and cannot be moved aside"
		halt "$r flew binary ${got:0:12}, pinned $(pinned_sha | cut -c1-12) (firmware rebuilt mid-campaign); run moved to $p"
	fi
}

scored_ok() { # 0 if run_NNN has a parseable chain_score.json and no SCORE_PENDING
	local d
	d=$D/$(runname "$1")
	[ ! -f "$d/SCORE_PENDING" ] && jq -e '.key1 and .key2' "$d/chain_score.json" >/dev/null 2>&1
}

# fault IDX ATTEMPT RC PARTIAL WHY: one FAULTS.tsv row; the moved attempt keeps a small chain_fault.txt (evidence to
# commit: g3_stdout.txt and the stream are ignored by pattern, so their tails are copied here)
fault() {
	local idx=$1 attempt=$2 rc=$3 p=$4 why=$5 f
	[ -s "$D/FAULTS.tsv" ] || printf 'time\tidx\tattempt\trc\tpartial\twhy\n' >"$D/FAULTS.tsv"
	printf '%s\t%03d\t%s\t%s\t%s\t%s\n' "$(ts)" "$idx" "$attempt" "$rc" "${p:--}" "$why" >>"$D/FAULTS.tsv"
	[ -n "$p" ] && [ -d "$D/$p" ] || return 0
	f=$D/$p/chain_fault.txt
	{
		echo "$(ts) idx=$idx attempt=$attempt rc=$rc: $why"
		echo "--- tail of g3_stdout.txt"
		tail -n 40 "$D/$p/g3_stdout.txt" 2>/dev/null | cut -c1-400
		echo "--- tail of stream_$(printf %03d "$idx").txt"
		tail -n 20 "$D/stream_$(printf %03d "$idx").txt" 2>/dev/null | cut -c1-400
	} >"$f"
}

fly() { # fly IDX ATTEMPT -> RESULT (ok|flight|other|void|failed|interrupted), WHY, RC, DUR
	local idx=$1 attempt=$2 r d t0 c cls p
	r=$(runname "$idx")
	d=$D/$r
	# partial run of a killed or failed flight: kept aside, flown into a clean directory
	p=$(move_partial "$idx") || halt "cannot move $r aside"
	[ -n "$p" ] && progress "idx=$idx moved leftover directory to $p"
	t0=$(date +%s)
	if [ -n "${G3_CHAIN_TEST_FLIGHT_CMD:-}" ]; then # TEST HOOK, see header
		run_bg "${CONTAINER_PREFIX}$(printf %03d "$idx")" "$D/stream_$(printf %03d "$idx").txt" \
			env OUT="$d" bash -c "$G3_CHAIN_TEST_FLIGHT_CMD"
	else
		run_bg "${CONTAINER_PREFIX}$(printf %03d "$idx")" "$D/stream_$(printf %03d "$idx").txt" \
			timeout "$FLIGHT_TIMEOUT_S" indi_project/docker/run.sh -n "${CONTAINER_PREFIX}$(printf %03d "$idx")" -t "$CONTAINER_TIMEOUT_S" -- \
			python3 indi_flight/bench/g3_run.py --seed "$SEED" --n "$N" --start "$idx" --stop "$idx" \
			--base-params "$PARAMS" --out-root "$DREL" --timeout-s "$RUN_TIMEOUT_S" --speed "$SPEED" \
			${SAMPLES:+--samples "$SAMPLES" --require-actc}
	fi
	DUR=$(($(date +%s) - t0))
	if [ -f "$d/g3_done.json" ]; then
		c=$(classify_done "$d/g3_done.json")
	else
		c="none rc=$RC$([ "$RC" = 124 ] && echo ' (timeout)'), no g3_done.json"
	fi
	cls=${c%% *}
	WHY=${c#* }
	[ "$WHY" = "$c" ] && WHY=
	case "$cls" in
	ok | flight) RESULT=$cls ;;
	other | void) # a kill can end a flight early: then it is an interruption, not a result
		if [ "$STOP_NOW" = 1 ]; then RESULT=interrupted; else RESULT=$cls; fi ;;
	*) if [ "$STOP_NOW" = 1 ]; then RESULT=interrupted; else RESULT=failed; fi ;; # infra, or no g3_done.json
	esac
	p=
	if [ "$RESULT" = failed ] || [ "$RESULT" = interrupted ]; then
		p=$(move_partial "$idx") || halt "cannot move $r aside"
		[ -n "$p" ] && WHY="$WHY; moved to $p"
	else
		echo "$c" >"$d/chain_class.txt"
	fi
	progress "idx=$idx attempt=$attempt rc=$RC dur=${DUR}s result=$RESULT${WHY:+ ($WHY)}"
	[ "$RESULT" = failed ] && fault "$idx" "$attempt" "$RC" "$p" "$c"
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
	if [ -n "${G3_CHAIN_TEST_SCORE_CMD:-}" ]; then # TEST HOOK, see header: no docker, the command writes chain_score.json
		OUT="$d" IDX="$idx" bash -c "$G3_CHAIN_TEST_SCORE_CMD" 8>&-
		rm -rf "$tmp"
		scored_ok "$idx" && progress "idx=$idx score (test hook) key1=$(jq -r .key1 "$d/chain_score.json") key2=$(jq -r .key2 "$d/chain_score.json")"
		scores_tsv
		return
	fi
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
	elif grep -qE "^$r INVALID" "$d/chain_key1.txt"; then
		# harness abort: key 2 writes its own INVALID json (window args are not used for an invalid run)
		python3 indi_flight/bench/g3_checks_key2.py "$DREL/$r" --t0 0 --t1 1 --out "$DREL/key2" >"$d/chain_key2.txt" 2>&1
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
lab = lambda j: "INVALID" if j.get("invalid") else ("pass" if j.get("pass") else "FAIL")  # INVALID = harness abort, re-fly (Q27 item 8)
s = {"idx": idx, "outcome": outcome, "key1": lab(k1), "key1_failing": [] if k1.get("invalid") else fail(k1),
     "key2": lab(k2), "key2_failing": [] if k2.get("invalid") else fail(k2),
     "key2_col5_g4_chatter_pass": None if k2.get("invalid") else k2.get("chatter", {}).get("pass"), "score_args": args,
     "scored": time.strftime("%F %T")}
tmp = os.path.join(rd, "chain_score.json.tmp")
with open(tmp, "w") as fh:
    json.dump(s, fh, indent=1)
os.replace(tmp, os.path.join(rd, "chain_score.json"))
PY
	if scored_ok "$idx"; then
		progress "idx=$idx score key1=$(jq -r .key1 "$d/chain_score.json") key2=$(jq -r .key2 "$d/chain_score.json")"
	else
		[ -f "$d/SCORE_PENDING" ] || echo "scoring step failed (see chain.log)" >"$d/SCORE_PENDING"
		progress "idx=$idx score=PENDING $(head -c 200 "$d/SCORE_PENDING")"
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
        if os.path.exists(os.path.join(rd, "CHAIN_FAILED")):  # infra fault twice (FAULTS.tsv has every attempt)
            why = " ".join(open(os.path.join(rd, "CHAIN_FAILED")).read().split())[:300]
            rows.append("\t".join([idx, "CHAIN_FAILED: " + why, "-", "-", "-", "-", "-"]))
        continue
    try:
        c = " ".join(open(os.path.join(rd, "chain_class.txt")).read().split())
        if c and c != "ok":
            o = f"{o} ({c[len(o) + 1:] if c.startswith(o + ' ') else c})"
    except OSError:
        pass
    try:
        if os.path.exists(os.path.join(rd, "SCORE_PENDING")):
            raise ValueError
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
	for p in "/proc/$BASHPID/fd"/*; do
		fd=${p##*/}
		[ "$fd" -gt 2 ] 2>/dev/null || continue
		[ "$(readlink "$p" 2>/dev/null)" = "$SELF" ] && continue
		eval "exec $fd>&-" 2>/dev/null
	done
}

# skip_done IDX: a finished run is kept unless it is an infra fault; binary checked; scored if needed.
# Returns 0 if kept (skip it), 1 if it must be flown.
skip_done() {
	local idx=$1 d c p
	d=$D/$(runname "$idx")
	c=$(classify_done "$d/g3_done.json")
	case "${c%% *}" in
	ok | flight | other | void) [ "$(cat "$d/chain_class.txt" 2>/dev/null)" = "$c" ] || echo "$c" >"$d/chain_class.txt" ;;
	*) # e.g. a flight finished by an orphan after a kill -9
		p=$(move_partial "$idx") || halt "cannot move $(runname "$idx") aside"
		progress "idx=$idx finished run is an infra fault (${c#* }): moved to $p, flown again"
		fault "$idx" skip "-" "$p" "$c"
		return 1
		;;
	esac
	check_binary "$idx"
	# a run scored here (not before the restart) is judged by --halt-on-fail like a freshly flown one; a run that was
	# already scored, such as the halting run after the operator removed CHAIN_HALTED, is not judged again
	scored_ok "$idx" || {
		score "$idx"
		[ "$STOP_NOW" = 1 ] || halt_on_fail_check "$idx"
	}
	return 0
}

# halt_on_fail_check IDX: with --halt-on-fail, halt when item 1 or item 2 is FAIL on both scoring keys of a scored run
halt_on_fail_check() {
	local idx=$1 d items src
	[ -f "$D/chain_halt_on_fail" ] || return 0
	d=$D/$(runname "$idx")
	case "$(cat "$d/chain_class.txt" 2>/dev/null)" in
	flight* | other*) # aborted run that is a flight result (O-12 watchdog or other), not infra: loss of control
		src=$(jq -r '.draw.source_run // "-"' "$d/g3_draw.json" 2>/dev/null)
		printf '{"status": "halted", "reason": "abort_flight", "idx": %d, "items": "abort_flight", "source_run": "%s", "time": "%s"}\n' "$idx" "$src" "$(ts)" >"$D/HALT_ON_FAIL.json"
		halt "HALT_ON_FAIL $(runname "$idx") (source run $src): abort_flight ($(cat "$d/chain_class.txt")); confirm by hand, then rm CHAIN_HALTED HALT_ON_FAIL.json to resume"
		;;
	esac
	if ! scored_ok "$idx"; then # SCORE_PENDING or no score file: the run cannot be judged, do not fly on
		printf '{"status": "halted", "reason": "score_pending", "idx": %d, "items": "score_pending", "source_run": "-", "time": "%s"}\n' "$idx" "$(ts)" >"$D/HALT_ON_FAIL.json"
		halt "HALT_ON_FAIL $(runname "$idx"): score_pending (see $(runname "$idx")/SCORE_PENDING, chain_key*.txt); rescore, then rm CHAIN_HALTED HALT_ON_FAIL.json to resume"
	fi
	items=$(jq -r '[.key1_failing, .key2_failing] | (.[0] - (.[0] - .[1])) | map(select(. == "item1" or . == "item2")) | join(",")' "$d/chain_score.json")
	[ -n "$items" ] || return 0
	src=$(jq -r '.draw.source_run // "-"' "$d/g3_draw.json" 2>/dev/null)
	printf '{"status": "halted", "idx": %d, "items": "%s", "source_run": "%s", "time": "%s"}\n' "$idx" "$items" "$src" "$(ts)" >"$D/HALT_ON_FAIL.json"
	halt "HALT_ON_FAIL $(runname "$idx") (source run $src): $items FAIL on both keys; confirm by hand (item 2: speed-1 re-fly), then rm CHAIN_HALTED HALT_ON_FAIL.json to resume"
}

run_chain() {
	close_inherited_fds
	exec 8>>"$LOCK"
	flock -w 10 8 || {
		echo "$(ts) lock busy, another chain runs: exit"
		exit 1
	}
	[ "$DREL" = "$DEFAULT_DIR" ] && echo "$DREL" >"$DIRFILE"
	CHAIN_PID=$$
	STARTED=$(ts)
	trap on_signal TERM INT
	read_campaign_range
	echo "$(ts) chain pid $$ sid $(ps -o sid= -p $$ | tr -d ' ') range $RANGE_A-$RANGE_B (campaign $CAMP_A-$CAMP_B) dir $DREL"
	kill_orphans
	progress "START pid=$$ range=$RANGE_A-$RANGE_B campaign=$CAMP_A-$CAMP_B speed=$SPEED binary=$(pinned_sha | cut -c1-12)${G3_CHAIN_TEST_FLIGHT_CMD:+ TEST_FLIGHT_CMD=$G3_CHAIN_TEST_FLIGHT_CMD}"
	write_status running
	local idx r d i bad=0 other=0 streak=() c0 avail reason p
	for idx in $(seq "$RANGE_A" "$RANGE_B"); do
		r=$(runname "$idx")
		d=$D/$r
		if [ -f "$D/STOP_CHAIN" ] || [ "$STOP_NOW" = 1 ]; then break; fi
		if [ -f "$d/g3_done.json" ]; then
			skip_done "$idx" && continue
		fi
		[ "$STOP_NOW" = 1 ] && break
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
				write_status running "$idx" "flying (attempt 2)"
				fly "$idx" 2
			fi
		fi
		if [ "$RESULT" = interrupted ]; then
			progress "idx=$idx INTERRUPTED (stop requested); flown again on the next start"
			break
		fi
		if [ "$RESULT" = failed ]; then
			mkdir -p "$d"
			echo "$(ts) infra fault twice: $WHY (rc $RC; attempts in partial/, FAULTS.tsv)" >"$d/CHAIN_FAILED"
			fault "$idx" CHAIN_FAILED "$RC" "" "infra fault on both attempts, last: $WHY"
			bad=$((bad + 1))
			streak+=("$idx")
		else
			check_binary "$idx"
			if [ "$RESULT" = void ]; then # validity failed: wrong controller/params, a set-up fault more than a result
				bad=$((bad + 1))
				streak+=("$idx")
			else
				bad=0
				streak=()
			fi
			if [ "$RESULT" = other ]; then other=$((other + 1)); else other=0; fi
			score "$idx"
			[ "$STOP_NOW" = 1 ] && break
			halt_on_fail_check "$idx"
		fi
		progress "idx=$idx cycle=$(($(date +%s) - c0))s"
		write_status running "$idx" flown
		if [ "$other" -ge "$MAX_CONSECUTIVE_OTHER" ]; then # the runs stay counted as results
			halt "$other consecutive aborted-other flight results (last idx $idx: ${WHY:-see progress.txt}); they are kept as results, check the set-up before going on"
		fi
		if [ "$bad" -ge "$MAX_CONSECUTIVE_BAD" ]; then
			# most likely docker/host trouble: clear the streak so a restart flies it again
			for i in "${streak[@]}"; do
				d=$D/$(runname "$i")
				if [ -f "$d/CHAIN_FAILED" ]; then
					rm -f "$d/CHAIN_FAILED"
					rmdir "$d" 2>/dev/null
				else
					p=$(move_partial "$i") || halt "cannot move void $(runname "$i") aside"
					progress "idx=$i void run moved to $p (breaker)"
				fi
			done
			halt "$bad consecutive infra-failed or void indices (${streak[*]}): host/docker/set-up trouble suspected, not a controller result; these indices were cleared (void runs moved to partial/) so a restart flies them again"
		fi
	done
	if [ "$STOP_NOW" = 1 ] || [ -f "$D/STOP_CHAIN" ]; then
		progress "STOPPED ($([ "$STOP_NOW" = 1 ] && echo now || echo after the current run))"
		rm -f "$D/STOP_CHAIN"
		write_status stopped
		exit 0
	fi
	local left
	write_status running
	left=$(jq -r '.remaining' "$D/chain_status.json" 2>/dev/null)
	scores_tsv
	if [ "${left:-1}" = 0 ]; then
		echo "$(ts) all campaign indices $CAMP_A-$CAMP_B have g3_done.json or CHAIN_FAILED; see SCORES.tsv" >"$D/CHAIN_FINISHED"
		progress "FINISHED campaign=$CAMP_A-$CAMP_B"
		write_status finished
	else
		progress "END of range $RANGE_A-$RANGE_B with $left campaign indices remaining"
		write_status stopped
	fi
	exit 0
}

# ---------------------------------------------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------------------------------------------
cmd_start() {
	local allow="" pos=() a speed="" samples="" haltfail=0
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
		--samples)
			samples=${2:-}
			[ -n "$samples" ] || die "--samples needs a directory"
			shift 2
			;;
		--halt-on-fail)
			haltfail=1
			shift
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
	if [ -s "$D/chain_range" ]; then
		read_campaign_range
	elif [ ${#pos[@]} -eq 3 ]; then
		CAMP_A=${pos[1]} CAMP_B=${pos[2]}
	else
		CAMP_A=0 CAMP_B=$((N - 1))
	fi
	if [ ${#pos[@]} -eq 3 ]; then
		RANGE_A=${pos[1]} RANGE_B=${pos[2]}
	else
		RANGE_A=$CAMP_A RANGE_B=$CAMP_B
	fi
	for a in "$RANGE_A" "$RANGE_B" "$CAMP_A" "$CAMP_B"; do [[ "$a" =~ ^[0-9]+$ ]] || die "bad index $a"; done
	if [ "$CAMP_A" -gt "$CAMP_B" ] || [ "$CAMP_B" -ge "$N" ]; then die "range must satisfy 0 <= first <= last < $N"; fi
	if [ "$RANGE_A" -gt "$RANGE_B" ] || [ "$RANGE_A" -lt "$CAMP_A" ] || [ "$RANGE_B" -gt "$CAMP_B" ]; then
		die "range $RANGE_A-$RANGE_B is not inside the campaign range $CAMP_A-$CAMP_B of $DREL (set at its first start)"
	fi

	if lock_held; then
		echo "g3_chain: refused, a chain (or rescore) already holds $LOCK" >&2
		D_SAVE=$D
		resolve_dir "$(default_dir)"
		print_status
		D=$D_SAVE
		exit 1
	fi
	if [ -n "${G3_CHAIN_TEST_FLIGHT_CMD:-}${G3_CHAIN_TEST_SCORE_CMD:-}" ]; then
		is_smoke || die "G3_CHAIN_TEST_FLIGHT_CMD / G3_CHAIN_TEST_SCORE_CMD are test hooks, refused outside a *smoke* directory"
	fi
	[ -f "$D/CHAIN_HALTED" ] && {
		cat "$D/CHAIN_HALTED" >&2
		die "refused: $DREL/CHAIN_HALTED exists (diagnose, then rm it)"
	}
	[ -f "$D/CHAIN_FINISHED" ] && die "refused: $DREL/CHAIN_FINISHED exists, nothing to fly"
	command -v docker >/dev/null || die "docker not found"
	[ -n "$(image_id)" ] || die "docker image $IMAGE not found"

	# samples dir: given at the first start of DIR, then pinned (a later start gives the same one, or none)
	if [ -n "$samples" ]; then
		local sabs
		sabs=$(cd "$OLDCWD" && realpath -m -- "$samples")
		case "$sabs" in
		"$REPO"/indi_flight/results/?*) samples=${sabs#"$REPO"/} ;;
		*) die "--samples must be under $REPO/indi_flight/results (got $sabs)" ;;
		esac
		[ -f "$REPO/$samples/index.json" ] || die "--samples $samples has no index.json"
	fi
	select_samples
	if [ -f "$D/chain_freeze.sha256" ]; then
		[ -z "$samples" ] || [ "$samples" = "$SAMPLES" ] || die "refused: --samples ${samples} differs from the samples pinned in $DREL (${SAMPLES:-none})"
	else
		SAMPLES=$samples
	fi
	select_params
	# freeze: the binary must be the FREEZE-10 gate binary (or the explicit override), and match the pins of DIR
	local cur
	cur=$(binary_sha)
	[ -n "$cur" ] || die "$BINARY missing"
	if [ -f "$D/chain_freeze.sha256" ]; then
		[ -z "$allow" ] || [ "$allow" = "$(pinned_sha)" ] || die "refused: --allow-binary ${allow:0:12} differs from the binary pinned in $DREL ($(pinned_sha | cut -c1-12)); one campaign, one binary"
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
	[ -s "$D/chain_range" ] || echo "$CAMP_A $CAMP_B" >"$D/chain_range"
	[ -f "$D/.gitignore" ] || printf '# chain scratch: scoring link directory, temporary files (partial/ is evidence: big files are ignored by the repo patterns)\n.score_tmp/\n*.tmp\n' >"$D/.gitignore"
	[ "$haltfail" = 0 ] || echo "item 1 or item 2 FAIL on both keys halts the chain" >"$D/chain_halt_on_fail"
	rm -f "$D/STOP_CHAIN"

	local inhibit=()
	command -v systemd-inhibit >/dev/null && inhibit=(systemd-inhibit --what=sleep:idle:handle-lid-switch
		--who="indi G3 flight chain" --why="G3 campaign flights running" --mode=block)
	# new session, no terminal, stdin /dev/null, inherited fds (the supervisor's lock fd 9 among them) closed
	# before systemd-inhibit; survives the caller's exit
	(
		close_inherited_fds
		RANGE_A=$RANGE_A RANGE_B=$RANGE_B exec setsid nohup "${inhibit[@]}" bash "$SELF" _run "$DREL" \
			</dev/null >>"$D/chain.log" 2>&1
	) &
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
	elif [[ ! "$(jq -r '.started // ""' "$D/chain_status.json" 2>/dev/null)" < "$launched" ]]; then
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

stop_chain_containers() {
	dk ps -q --filter "name=^px4-indi-${CONTAINER_PREFIX}" | xargs -r timeout "$DOCKER_TIMEOUT_S" docker stop -t 10 >/dev/null
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
		lock_held || stop_chain_containers
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
	stop_chain_containers # anything a dying chain left behind
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
		idx=$((10#${d##*_}))
		scored_ok "$idx" && continue
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

OLDCWD=${OLDPWD:-$REPO}
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
	select_samples
	select_params
	run_chain
	;;
*)
	sed -n '2,19p' "$SELF" | sed 's/^# \{0,1\}//'
	exit 64
	;;
esac
