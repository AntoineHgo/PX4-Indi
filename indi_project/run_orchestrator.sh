#!/usr/bin/env bash
# Relaunches the orchestrator until it creates indi_project/DONE.
# Each launch is a fresh session that resumes from indi_project/STATE.md.
# Stop it gracefully with: touch indi_project/STOP
# Lift the 5-hour usage share on demand with: touch indi_project/BYPASS_5H (rm it to restore)
set -u
export LC_NUMERIC=C # decimal point in awk and printf, whatever the host locale
cd "$(dirname "$0")/.."
REPO=$PWD

# keep the host awake for the whole supervision (the first run lost 7 h to a laptop suspend)
if [ -z "${INDI_INHIBITED:-}" ] && command -v systemd-inhibit >/dev/null; then
	export INDI_INHIBITED=1
	exec systemd-inhibit --what=sleep:idle:handle-lid-switch --who="indi orchestrator" \
		--why="unattended INDI orchestrator running" --mode=block "$REPO/indi_project/run_orchestrator.sh" "$@"
fi

PROMPT_FILE=indi_project/ORCHESTRATOR_PROMPT.md
GUARD=indi_project/guard.sh
LOG_DIR=indi_project/logs
MODEL="${MODEL:-claude-opus-5-5}"
EFFORT="${EFFORT:-high}"
BRANCH="${BRANCH:-feat/indi-control}"
EXPECTED_ORIGIN="${EXPECTED_ORIGIN:-AntoineHgo/PX4-Indi}"
# Share of the owner's usage the orchestrator may take. Before each launch a tiny Haiku call
# (~$0.002) reads the current utilization of the 5-hour and weekly windows; the orchestrator
# only launches below these shares, and its spend cap is the headroom left in the 5-hour share.
FIVE_HOUR_SHARE="${FIVE_HOUR_SHARE:-0.8}"  # leave the top 20 % of every 5-hour window to the owner
WEEKLY_SHARE="${WEEKLY_SHARE:-0.6}"        # stop launching once the weekly window is 60 % used
MIN_BUDGET_USD="${MIN_BUDGET_USD:-1}"      # below this headroom a session is mostly start-up cost: wait instead
MAX_BUDGET_USD="${MAX_BUDGET_USD:-3}"      # bounds what one cut-off session can lose
# Usage left in a 5-hour window is lost at its reset, so in its last FINAL_STRETCH_S seconds the
# orchestrator may use the whole window (share 1.0). The owner can lift the 5-hour share at any
# time with `touch indi_project/BYPASS_5H` (remove the file to restore it); the supervisor checks
# the file every minute, even while waiting. The weekly share still applies in both cases.
FINAL_STRETCH_S="${FINAL_STRETCH_S:-3600}"
BYPASS_FILE=indi_project/BYPASS_5H
WINDOW_USD_DEFAULT=9                       # $ per full 5-hour window, measured on session 1; recalibrated each run
LIMIT_WAIT="${LIMIT_WAIT:-1800}"           # fallback wait after a failed or very short run
MAX_RUNS="${MAX_RUNS:-300}"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG_DIR/supervisor.log"; }
die() { log "ABORT: $*"; exit 1; }

# sleep until an epoch time by wall clock (bash sleep stops counting during a suspend);
# returns early if STOP or DONE appears, or if BYPASS_5H appears while it was absent
wait_until() {
	local bypass_at_start=0
	[ -f "$BYPASS_FILE" ] && bypass_at_start=1
	while [ "$(date +%s)" -lt "$1" ]; do
		{ [ -f indi_project/DONE ] || [ -f indi_project/STOP ]; } && return
		[ "$bypass_at_start" -eq 0 ] && [ -f "$BYPASS_FILE" ] && return
		sleep 60 9>&-
	done
}

# floating-point helpers
fcalc() { awk "BEGIN { printf \"%.2f\", $1 }"; }
fge() { awk "BEGIN { exit !($1 >= $2) }"; }

# last rate_limit_info of a tiny Haiku call: current utilization of every usage window
probe_usage() {
	claude -p "Reply with the single word ok." --model claude-haiku-5-5 --effort low \
		--no-session-persistence --max-budget-usd 0.05 --output-format stream-json --verbose 2>/dev/null 9>&- |
		jq -c 'select(.type=="rate_limit_event") | .rate_limit_info' | tail -1
}

window_usd() {
	local w
	w=$(cat "$LOG_DIR/window_usd" 2>/dev/null)
	echo "${w:-$WINDOW_USD_DEFAULT}"
}

# after a run: $ per 5-hour window = run cost / 5-hour utilization it consumed (same window only)
calibrate_window() {
	local f=$1 cost=$2 first last
	first=$(jq -c 'select(.type=="rate_limit_event") | .rate_limit_info.unifiedWindows.five_hour // empty' "$f" | head -1)
	last=$(jq -c 'select(.type=="rate_limit_event") | .rate_limit_info.unifiedWindows.five_hour // empty' "$f" | tail -1)
	[ -n "$first" ] && [ -n "$last" ] && [ "$cost" != "?" ] || return
	[ "$(jq -r .resetsAt <<<"$first")" = "$(jq -r .resetsAt <<<"$last")" ] || return
	local du
	du=$(fcalc "$(jq -r .utilization <<<"$last") - $(jq -r .utilization <<<"$first")")
	fge "$du" 0.15 || return # too small a sample to be meaningful
	local w
	w=$(fcalc "$cost / $du")
	fge "$w" 3 && fge 50 "$w" || return
	echo "$w" >"$LOG_DIR/window_usd"
	log "calibration: a 5-hour window holds about \$$w (run used $du of it for \$$cost)"
}

# --- preflight: refuse to start unless the guards are in place ---
for tool in claude jq docker git realpath; do
	command -v "$tool" >/dev/null || die "$tool not found"
done

exec 9>"$LOG_DIR/.lock"
flock -n 9 || die "another supervisor is already running"

case "$(git remote get-url origin)" in
*"$EXPECTED_ORIGIN"*) ;;
*) die "origin is not $EXPECTED_ORIGIN" ;;
esac

# the agent may push to origin only; make pushing anywhere else impossible
if git remote get-url upstream >/dev/null 2>&1; then
	git remote set-url --push upstream DISABLED
fi

guard_blocks() {
	jq -n --arg c "$1" --arg d "$REPO" '{tool_name:"Bash", cwd:$d, tool_input:{command:$c}}' | "$GUARD" >/dev/null 2>&1
	[ $? -eq 2 ]
}
[ -x "$GUARD" ] || die "$GUARD is not executable"
guard_blocks "sudo true" || die "guard self-test failed (sudo)"
guard_blocks "git push --force origin $BRANCH" || die "guard self-test failed (force push)"
guard_blocks "git push origin main" || die "guard self-test failed (push to main)"
guard_blocks "rm -rf /home" || die "guard self-test failed (rm)"
guard_blocks "ls" && die "guard self-test failed (blocks everything)"

if [ "$(git branch --show-current)" != "$BRANCH" ]; then
	git switch "$BRANCH" 2>/dev/null || git switch -c "$BRANCH" || die "cannot switch to $BRANCH"
fi
log "preflight ok: branch $BRANCH, model $MODEL, effort $EFFORT, shares 5h $FIVE_HOUR_SHARE (1.0 in the last ${FINAL_STRETCH_S}s or with $BYPASS_FILE) / weekly $WEEKLY_SHARE, cap \$$MIN_BUDGET_USD-$MAX_BUDGET_USD/session, $(claude --version 2>/dev/null)"

# --- supervise ---
runs=0
while [ ! -f indi_project/DONE ] && [ ! -f indi_project/STOP ]; do
	# --- usage gate: launch only within the orchestrator's share of the owner's usage ---
	now=$(date +%s)
	rl=$(probe_usage)
	if [ -z "$rl" ]; then
		log "usage probe failed (network or hard limit), retrying in ${LIMIT_WAIT}s"
		wait_until $((now + LIMIT_WAIT))
		continue
	fi
	u5=$(jq -r '.unifiedWindows.five_hour.utilization // 0' <<<"$rl")
	r5=$(jq -r ".unifiedWindows.five_hour.resetsAt // $((now + LIMIT_WAIT))" <<<"$rl")
	u7=$(jq -r '.unifiedWindows.seven_day.utilization // 0' <<<"$rl")
	r7=$(jq -r ".unifiedWindows.seven_day.resetsAt // $((now + LIMIT_WAIT))" <<<"$rl")
	rejected=$(jq -r '[.unifiedWindows // {} | to_entries[] | select(.value.status == "rejected") | .value.resetsAt] | max // empty' <<<"$rl")
	w=$(window_usd)
	share=$FIVE_HOUR_SHARE
	share_why=""
	if [ -f "$BYPASS_FILE" ]; then
		share=1
		share_why=", share lifted by $BYPASS_FILE"
	elif [ $((r5 - now)) -le "$FINAL_STRETCH_S" ]; then
		share=1
		share_why=", last $((FINAL_STRETCH_S / 60)) min before the reset: full window"
	fi
	headroom=$(fcalc "($share - $u5) * $w")
	log "usage: 5-hour $u5, weekly $u7, headroom \$$headroom (window \$$w, share $share$share_why)"
	if [ -n "$rejected" ]; then
		log "a usage window is exhausted, waiting until $(date -d "@$rejected" '+%F %T')"
		wait_until $((rejected + 120))
		continue
	fi
	if fge "$u7" "$WEEKLY_SHARE"; then
		log "weekly window at $u7 >= share $WEEKLY_SHARE, waiting for its reset at $(date -d "@$r7" '+%F %T')"
		wait_until $((r7 + 120))
		continue
	fi
	if ! fge "$headroom" "$MIN_BUDGET_USD"; then
		stretch=$((r5 - FINAL_STRETCH_S))
		if [ "$share" != 1 ] && [ "$stretch" -gt "$now" ]; then
			log "5-hour headroom below \$$MIN_BUDGET_USD, waiting for the last stretch before its reset at $(date -d "@$stretch" '+%F %T')"
			wait_until $((stretch + 60))
		else
			log "5-hour headroom below \$$MIN_BUDGET_USD, waiting for its reset at $(date -d "@$r5" '+%F %T')"
			wait_until $((r5 + 120))
		fi
		continue
	fi
	budget=$headroom
	fge "$budget" "$MAX_BUDGET_USD" && budget=$MAX_BUDGET_USD

	runs=$((runs + 1))
	[ "$runs" -le "$MAX_RUNS" ] || die "reached MAX_RUNS=$MAX_RUNS"
	ts=$(date +%Y%m%d-%H%M%S)
	start=$(date +%s)
	log "run $runs: launching orchestrator with a \$$budget cap (log: $LOG_DIR/run-$ts.jsonl)"

	prompt="$(cat "$PROMPT_FILE")

## This session

- Launch $ts, model $MODEL. Spend cap for this session: about \$$budget, subagents included.
  When it is reached the session is cut off and running subagents are stopped, so save state and
  commit before starting anything long, and size the work you launch to fit."

	claude -p "$prompt" \
		--name "indi-orchestrator $ts" \
		--model "$MODEL" \
		--effort "$EFFORT" \
		--max-budget-usd "$budget" \
		--settings indi_project/claude_settings.json \
		--dangerously-skip-permissions \
		--output-format stream-json --verbose \
		> "$LOG_DIR/run-$ts.jsonl" 2> "$LOG_DIR/run-$ts.err" 9>&-
	rc=$?
	elapsed=$(($(date +%s) - start))
	result=$(jq -c 'select(.type=="result")' "$LOG_DIR/run-$ts.jsonl" 2>/dev/null | tail -1)
	subtype=$(jq -r '.subtype // "?"' <<<"$result" 2>/dev/null)
	cost=$(jq -r '.total_cost_usd // "?"' <<<"$result" 2>/dev/null)
	session=$(jq -r '.session_id // "?"' <<<"$result" 2>/dev/null)
	log "run $runs: exit $rc after ${elapsed}s, result $subtype, cost \$${cost:-?}, session $session"
	calibrate_window "$LOG_DIR/run-$ts.jsonl" "${cost:-?}"

	# the usage gate at the top of the loop decides whether the next launch has room;
	# here only guard against a session that fails straight away for another reason
	if [ "$rc" -eq 0 ] || [ "$elapsed" -ge 300 ] || [ "$subtype" = "error_max_budget_usd" ]; then
		wait_s=60
	else
		wait_s=$LIMIT_WAIT
	fi

	{ [ -f indi_project/DONE ] || [ -f indi_project/STOP ]; } && break
	log "relaunching in ${wait_s}s (at $(date -d "@$(($(date +%s) + wait_s))" '+%F %T'))"
	wait_until $(($(date +%s) + wait_s))
done

if [ -f indi_project/DONE ]; then
	log "orchestrator reported completion, see indi_project/STATE.md"
else
	log "stopped by indi_project/STOP"
fi
