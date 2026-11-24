#!/usr/bin/env bash
# Relaunches the orchestrator until it creates indi_flight/DONE.
# Each launch is a fresh session that resumes from indi_flight/STATE.md (stage 2 of the INDI work; the stage-1 archive is indi_project/, read-only).
# Stop it gracefully with: touch indi_flight/STOP
# It pauses while indi_flight/WAIT_OWNER exists (the orchestrator creates it with a blocking question in
# indi_flight/QUESTIONS.md; the owner answers there and removes the file).
# Lift the 5-hour usage share on demand with: touch indi_flight/BYPASS_5H (rm it to restore)
# Lift the weekly usage share the same way with: touch indi_flight/BYPASS_7D (rm it to restore)
# Change the usage targets without a restart by editing indi_flight/USAGE_TARGETS (owner only, see below).
set -u
export LC_NUMERIC=C # decimal point in awk and printf, whatever the host locale
cd "$(dirname "$0")/.."
REPO=$PWD

# keep the host awake for the whole supervision (the first run lost 7 h to a laptop suspend)
if [ -z "${INDI_INHIBITED:-}" ] && command -v systemd-inhibit >/dev/null; then
	export INDI_INHIBITED=1
	exec systemd-inhibit --what=sleep:idle:handle-lid-switch --who="indi orchestrator" \
		--why="unattended INDI orchestrator running" --mode=block "$REPO/indi_flight/run_orchestrator.sh" "$@"
fi

PROMPT_FILE=indi_flight/MISSION.md
GUARD=indi_flight/guard.sh
LOG_DIR=indi_flight/logs
MODEL="${MODEL:-claude-opus-5-5}"
EFFORT="${EFFORT:-high}"
BRANCH="${BRANCH:-feat/indi-flight}"
EXPECTED_ORIGIN="${EXPECTED_ORIGIN:-AntoineHgo/PX4-Indi}"
# Share of the owner's usage the orchestrator may take. Before each launch a tiny Haiku call
# (~$0.002) reads the current utilization of the 5-hour and weekly windows; the orchestrator
# only launches below these shares, and its spend cap is the smaller of the headroom left in the
# 5-hour share, the headroom left under the weekly limit, and MAX_BUDGET_USD.
# The values below are defaults (environment variables override them). The owner's file
# indi_flight/USAGE_TARGETS overrides both; it is re-read before every launch and every minute while
# the supervisor waits, so a change applies without a restart. One key=value per line, # comments:
#   five_hour=0.8          share of each 5-hour window (FIVE_HOUR_SHARE)
#   weekly=0.9             share of the weekly window (WEEKLY_SHARE)
#   max_session_usd=6      spend cap of one session (MAX_BUDGET_USD)
#   weekly_pacing=on       on: the weekly limit grows with the week (WEEKLY_PACING)
#   pace_slack=0.15        pacing lead, as a fraction of the week (PACE_SLACK)
# With pacing on, the weekly limit at a time t is weekly x min(1, elapsed fraction of the week + slack),
# so the orchestrator cannot use the whole weekly share early and leave the owner nothing for the
# remaining days. Invalid values are ignored (logged) and the previous value is kept.
FIVE_HOUR_SHARE="${FIVE_HOUR_SHARE:-0.8}"  # leave the top 20 % of every 5-hour window to the owner
WEEKLY_SHARE="${WEEKLY_SHARE:-0.7}"        # stop launching once the weekly window is 70 % used
WEEKLY_PACING="${WEEKLY_PACING:-on}"
PACE_SLACK="${PACE_SLACK:-0.15}"           # about one day ahead of an even spread
MIN_BUDGET_USD="${MIN_BUDGET_USD:-1}"      # below this headroom a session is mostly start-up cost: wait instead
MAX_BUDGET_USD="${MAX_BUDGET_USD:-6}"     # bounds what one cut-off session can lose
TARGETS_FILE=indi_flight/USAGE_TARGETS
# Usage left in a 5-hour window is lost at its reset, so in its last FINAL_STRETCH_S seconds the
# orchestrator may use the whole window (share 1.0). The owner can lift the 5-hour share at any
# time with `touch indi_flight/BYPASS_5H` (remove the file to restore it); the supervisor checks
# the file every minute, even while waiting. The weekly share still applies in both cases, unless
# the owner also touches indi_flight/BYPASS_7D, which skips the weekly gate (only the owner creates it;
# a window the API reports as exhausted still stops the launch).
FINAL_STRETCH_S="${FINAL_STRETCH_S:-3600}"
BYPASS_FILE=indi_flight/BYPASS_5H
BYPASS_7D_FILE=indi_flight/BYPASS_7D
WINDOW_USD_DEFAULT=9                       # $ per full 5-hour window, measured on session 1; recalibrated each run
WEEK_USD_DEFAULT=140                       # $ per full weekly window (2026-11-23: ~$13 of sessions for 0.81 -> 0.90);
                                           # recalibrated from the runs of each weekly window
WEEK_S=604800
LIMIT_WAIT="${LIMIT_WAIT:-1800}"           # fallback wait after a failed or very short run
# Token economy: every API turn re-reads the whole context. The session gets only the tools the
# orchestrator uses (the full default set and its descriptions took the start-up context to ~45k
# tokens), and STATE.md, read at every launch, has a size budget the session prompt enforces.
TOOLS="${TOOLS:-Bash,Read,Edit,Write,Task,Monitor,TaskStop,SendMessage,Skill,ToolSearch,WebSearch,WebFetch}"
STATE_MAX_BYTES="${STATE_MAX_BYTES:-8000}" # bytes; the session prompt asks for a trim above it
MAX_RUNS="${MAX_RUNS:-300}"
CHAIN_DIR=indi_flight/results/g3_campaign_f10 # the G3 campaign of indi_flight/bench/g3_chain.sh (lock in $LOG_DIR)
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG_DIR/supervisor.log"; }
die() { log "ABORT: $*"; exit 1; }

# signature of the owner's targets file: changes when it is created, edited or removed
targets_sig() { stat -c '%Y %s' "$TARGETS_FILE" 2>/dev/null || echo absent; }

# sleep until an epoch time by wall clock (bash sleep stops counting during a suspend);
# returns early if STOP or DONE appears, if BYPASS_5H or BYPASS_7D appears while it was absent,
# or if the owner changes USAGE_TARGETS (the loop then re-reads it and re-checks the gate)
wait_until() {
	local bypass_at_start=0 bypass7_at_start=0 sig_at_start
	[ -f "$BYPASS_FILE" ] && bypass_at_start=1
	[ -f "$BYPASS_7D_FILE" ] && bypass7_at_start=1
	sig_at_start=$(targets_sig)
	while [ "$(date +%s)" -lt "$1" ]; do
		{ [ -f indi_flight/DONE ] || [ -f indi_flight/STOP ]; } && return
		[ "$bypass_at_start" -eq 0 ] && [ -f "$BYPASS_FILE" ] && return
		[ "$bypass7_at_start" -eq 0 ] && [ -f "$BYPASS_7D_FILE" ] && return
		[ "$(targets_sig)" != "$sig_at_start" ] && { log "$TARGETS_FILE changed, re-checking the usage gate"; return; }
		sleep 60 9>&-
	done
}

# floating-point helpers
fcalc() { awk "BEGIN { printf \"%.2f\", $1 }"; }
fge() { awk "BEGIN { exit !($1 >= $2) }"; }
isnum() { [[ $1 =~ ^[0-9]+([.][0-9]+)?$|^[.][0-9]+$ ]]; }

# effective targets: defaults (environment) overlaid with the owner's USAGE_TARGETS; sets T5, T7,
# TMAX, TPACE, TSLACK and logs them whenever they change (warnings once per file version)
T5=$FIVE_HOUR_SHARE T7=$WEEKLY_SHARE TMAX=$MAX_BUDGET_USD TPACE=$WEEKLY_PACING TSLACK=$PACE_SLACK
targets_logged=''
targets_warned=''
load_targets() {
	local sig key val ok line src=defaults warn=""
	T5=$FIVE_HOUR_SHARE T7=$WEEKLY_SHARE TMAX=$MAX_BUDGET_USD TPACE=$WEEKLY_PACING TSLACK=$PACE_SLACK
	sig=$(targets_sig)
	if [ -f "$TARGETS_FILE" ]; then
		src=$TARGETS_FILE
		while IFS= read -r line || [ -n "$line" ]; do
			line=${line%%#*}
			[[ $line =~ ^[[:space:]]*$ ]] && continue
			if ! [[ $line =~ ^[[:space:]]*([a-z_0-9]+)[[:space:]]*=[[:space:]]*([^[:space:]]+)[[:space:]]*$ ]]; then
				warn="$warn; unreadable line '$line'"
				continue
			fi
			key=${BASH_REMATCH[1]} val=${BASH_REMATCH[2]} ok=
			case "$key" in
			five_hour) isnum "$val" && fge "$val" 0.01 && fge 1 "$val" && T5=$val ok=1 ;;
			weekly) isnum "$val" && fge "$val" 0.01 && fge 1 "$val" && T7=$val ok=1 ;;
			max_session_usd) isnum "$val" && fge "$val" "$MIN_BUDGET_USD" && fge 100 "$val" && TMAX=$val ok=1 ;;
			weekly_pacing) [[ $val == on || $val == off ]] && TPACE=$val ok=1 ;;
			pace_slack) isnum "$val" && fge 1 "$val" && TSLACK=$val ok=1 ;;
			*) warn="$warn; unknown key $key" ok=skip ;;
			esac
			[ -z "$ok" ] && warn="$warn; invalid $key=$val (default kept)"
		done <"$TARGETS_FILE"
	fi
	if [ -n "$warn" ] && [ "$targets_warned" != "$sig" ]; then
		log "WARNING $TARGETS_FILE: ${warn#; }"
	fi
	targets_warned=$sig
	local now_t="targets: 5h $T5, weekly $T7, pacing $TPACE (slack $TSLACK), session cap \$$TMAX (from $src)"
	[ "$now_t" = "$targets_logged" ] || log "$now_t"
	targets_logged=$now_t
}

# weekly limit now: T7, or with pacing T7 x min(1, elapsed fraction of the week + slack); $1 = weekly reset epoch
weekly_limit() {
	if [ "$TPACE" = on ]; then
		awk -v t="$T7" -v s="$TSLACK" -v r="$1" -v n="$(date +%s)" -v w="$WEEK_S" \
			'BEGIN { f = 1 - (r - n) / w; if (f < 0) f = 0; f += s; if (f > 1) f = 1; printf "%.3f", t * f }'
	else
		echo "$T7"
	fi
}

# epoch at which the paced weekly limit reaches utilization $1 (reset epoch $2); empty if only the reset will do
pace_reaches() {
	awk -v u="$1" -v t="$T7" -v s="$TSLACK" -v r="$2" -v w="$WEEK_S" \
		'BEGIN { if (u > t) exit; f = u / t - s; if (f < 0) f = 0; if (f >= 1) exit; printf "%d", r - w + f * w }'
}

week_usd() {
	local w
	w=$(cat "$LOG_DIR/week_usd" 2>/dev/null)
	echo "${w:-$WEEK_USD_DEFAULT}"
}

# after a run: $ per weekly window. Weekly utilization comes in steps of 0.01 and one run moves it by
# about 0.02, so runs of the same weekly window are summed (logs/week_calib: resetsAt cost_sum du_sum runs)
# and the ratio is written once their sum reaches 0.05. Only the runs' own spans count (not the owner's use between them).
calibrate_week() {
	local f=$1 cost=$2 first last r du
	first=$(jq -c 'select(.type=="rate_limit_event") | .rate_limit_info.unifiedWindows.seven_day // empty' "$f" | head -1)
	last=$(jq -c 'select(.type=="rate_limit_event") | .rate_limit_info.unifiedWindows.seven_day // empty' "$f" | tail -1)
	[ -n "$first" ] && [ -n "$last" ] && isnum "$cost" || return
	r=$(jq -r .resetsAt <<<"$first")
	[ "$r" = "$(jq -r .resetsAt <<<"$last")" ] || return
	du=$(awk -v a="$(jq -r .utilization <<<"$first")" -v b="$(jq -r .utilization <<<"$last")" 'BEGIN { printf "%.4f", b - a }')
	local cr='' cs ds n
	[ -f "$LOG_DIR/week_calib" ] && read -r cr cs ds n <"$LOG_DIR/week_calib"
	[ "${cr:-}" = "$r" ] || { cs=0 ds=0 n=0; }
	cs=$(awk -v a="$cs" -v b="$cost" 'BEGIN { printf "%.4f", a + b }')
	ds=$(awk -v a="$ds" -v b="$du" 'BEGIN { printf "%.4f", a + b }')
	n=$((n + 1))
	echo "$r $cs $ds $n" >"$LOG_DIR/week_calib"
	fge "$ds" 0.05 || return
	local w
	w=$(fcalc "$cs / $ds")
	fge "$w" 30 && fge 2000 "$w" || return
	echo "$w" >"$LOG_DIR/week_usd"
	log "calibration: a weekly window holds about \$$w ($n runs of this week used $ds of it for \$$cs)"
}

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
log "preflight ok: branch $BRANCH, model $MODEL, effort $EFFORT, shares 5h $FIVE_HOUR_SHARE (1.0 in the last ${FINAL_STRETCH_S}s or with $BYPASS_FILE) / weekly $WEEKLY_SHARE (lifted with $BYPASS_7D_FILE), cap \$$MIN_BUDGET_USD-$MAX_BUDGET_USD/session, $(claude --version 2>/dev/null)"
load_targets # logs the effective targets (USAGE_TARGETS overrides the defaults above)

# --- supervise ---
runs=0
while [ ! -f indi_flight/DONE ] && [ ! -f indi_flight/STOP ]; do
	# the orchestrator asked the owner a blocking question (indi_flight/QUESTIONS.md): wait, spending nothing
	if [ -f indi_flight/WAIT_OWNER ]; then
		[ -n "${waiting_logged:-}" ] || log "waiting for the owner: answer in indi_flight/QUESTIONS.md, then rm indi_flight/WAIT_OWNER"
		waiting_logged=1
		sleep 60 9>&-
		continue
	fi
	waiting_logged=
	# the detached G3 flight chain holds this lock while it flies: no session meanwhile (sequential rule, freeze),
	# unless the campaign chain is alive but its status is over an hour old (stuck: a session diagnoses it)
	chain_stuck=
	if [ -f "$LOG_DIR/flight_chain.lock" ] && ! flock -n "$LOG_DIR/flight_chain.lock" true 9>&-; then
		# stuck = the campaign chain itself is alive, says running, and has not updated its status for an hour
		chain_upd=$(jq -r 'select(.state == "running") | "\(.pid) \(.updated)"' "$CHAIN_DIR/chain_status.json" 2>/dev/null)
		if [ -n "$chain_upd" ] && kill -0 "${chain_upd%% *}" 2>/dev/null; then
			chain_upd=$(date -d "${chain_upd#* }" +%s 2>/dev/null)
		else
			chain_upd= # another chain (or a rescore) holds the lock: idle
		fi
		if [ -z "$chain_upd" ] || [ $(($(date +%s) - chain_upd)) -lt 3600 ]; then
			[ -n "${chain_logged:-}" ] || log "G3 flight chain flying, no session until it stops"
			chain_logged=1
			sleep 60 9>&-
			continue
		fi
		chain_stuck=1
		log "G3 flight chain holds its lock but $CHAIN_DIR/chain_status.json is over 1 h old: launching a session to diagnose"
	fi
	chain_logged=
	# --- usage gate: launch only within the orchestrator's share of the owner's usage ---
	load_targets
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
	wk=$(week_usd)
	share=$T5
	share_why=""
	if [ -f "$BYPASS_FILE" ]; then
		share=1
		share_why=", share lifted by $BYPASS_FILE"
	elif [ $((r5 - now)) -le "$FINAL_STRETCH_S" ]; then
		share=1
		share_why=", last $((FINAL_STRETCH_S / 60)) min before the reset: full window"
	fi
	headroom=$(fcalc "($share - $u5) * $w")
	lim7=$(weekly_limit "$r7")
	if [ -f "$BYPASS_7D_FILE" ]; then
		headroom7=
		lim_why="lifted by $BYPASS_7D_FILE"
	else
		headroom7=$(fcalc "($lim7 - $u7) * $wk")
		lim_why="target $T7$([ "$TPACE" = on ] && echo ", paced")"
	fi
	log "usage: 5-hour $u5, weekly $u7, headroom \$$headroom (window \$$w, share $share$share_why); weekly limit $lim7 ($lim_why), weekly headroom \$${headroom7:-none} (week \$$wk)"
	if [ -n "$rejected" ]; then
		log "a usage window is exhausted, waiting until $(date -d "@$rejected" '+%F %T')"
		wait_until $((rejected + 120))
		continue
	fi
	if [ -f "$BYPASS_7D_FILE" ]; then
		log "weekly window at $u7, share $T7 lifted by $BYPASS_7D_FILE"
	elif ! fge "$headroom7" "$MIN_BUDGET_USD"; then
		# with pacing, wait until the limit has grown by at least the minimum session; else for the reset
		pace_t=
		[ "$TPACE" = on ] && pace_t=$(pace_reaches "$(awk -v u="$u7" -v m="$MIN_BUDGET_USD" -v k="$wk" 'BEGIN { printf "%.4f", u + m / k }')" "$r7")
		if [ -n "$pace_t" ] && [ "$pace_t" -lt "$r7" ]; then
			[ "$pace_t" -gt "$now" ] || pace_t=$((now + 60))
			log "weekly window at $u7 >= paced limit $lim7 (target $T7), waiting for the pace until $(date -d "@$pace_t" '+%F %T')"
			wait_until $((pace_t + 60))
		else
			log "weekly window at $u7 >= share $T7, waiting for its reset at $(date -d "@$r7" '+%F %T')"
			wait_until $((r7 + 120))
		fi
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
	# spend cap: the smallest of the 5-hour headroom, the weekly headroom and the session cap
	budget=$headroom
	[ -n "$headroom7" ] && fge "$budget" "$headroom7" && budget=$headroom7
	fge "$budget" "$TMAX" && budget=$TMAX

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
	state_bytes=$(wc -c 2>/dev/null <indi_flight/STATE.md || echo 0)
	if [ "$state_bytes" -gt "$STATE_MAX_BYTES" ]; then
		prompt="$prompt
- indi_flight/STATE.md is $state_bytes bytes, over its $STATE_MAX_BYTES-byte budget. Before other work, move finished
  history to JOURNAL.md and lessons to LESSONS_PROPOSED.md, then commit. Next actions hold open work only."
		log "run $runs: STATE.md is $state_bytes bytes (budget $STATE_MAX_BYTES), the orchestrator is told to trim it"
	fi
	# results/ must end every session clean: each path committed or ignored (owner rule, 2026-11-18)
	dirty_results=$(git status --porcelain --untracked-files=all -- indi_flight/results 2>/dev/null)
	if [ -n "$dirty_results" ]; then
		n_dirty=$(wc -l <<<"$dirty_results")
		dirty_dirs=$(sed -E 's/^...//; s/^"//; s#^indi_flight/results/([^/]+).*#\1#' <<<"$dirty_results" | sort | uniq -c | sort -rn | head -25 |
			awk '{printf "    %s (%d)\n", $2, $1}')
		prompt="$prompt
- indi_flight/results has $n_dirty uncommitted or untracked paths (git status --porcelain -uall indi_flight/results).
  Owner rule: every path under indi_flight/results is either committed or ignored at the end of each session.
  Before other work, sort them: commit evidence (metrics, run.json, READMEs, scripts, plots and small CSVs a note
  cites); add raw captures and files over 1 MB to indi_flight/.gitignore by pattern; then commit. Only the output
  of a flight (or flight-chain run) still running may stay dirty, and its directory must be named in STATE.md. Directories (paths):
$dirty_dirs"
		log "run $runs: indi_flight/results has $n_dirty dirty paths, the orchestrator is told to commit or ignore them"
	fi
	# G3 campaign chain (indi_flight/bench/g3_chain.sh): the loop idles while it flies; other chain dirs are ignored
	chain_dir=$CHAIN_DIR
	if [ -f "$chain_dir/chain_status.json" ]; then
		if [ -n "$chain_stuck" ]; then
			chain_line="- G3 chain $chain_dir holds its lock but its chain_status.json is over 1 h old: run bash indi_flight/bench/g3_chain.sh status, diagnose (stuck flight or scorer), stop --now if needed."
		elif [ -f "$chain_dir/CHAIN_FINISHED" ]; then
			chain_line="- G3 chain $chain_dir finished: commit its runs, g3_chain.sh rescore (in the background) if any run is unscored, then the G3 verdict per GATES (skip if written)."
		else
			chain_line="- G3 chain $chain_dir is not running and unfinished: do not modify files listed in its chain_freeze.sha256 or switch branches over them. Commit its finished runs."
			if [ -f "$chain_dir/CHAIN_HALTED" ]; then
				chain_line="$chain_line It halted: $chain_dir/CHAIN_HALTED gives the reason; diagnosing it is the first task."
			else
				chain_line="$chain_line Run bash indi_flight/bench/g3_chain.sh status; unless STATE.md says it was stopped on purpose, start resumes it."
			fi
		fi
		prompt="$prompt
$chain_line"
		log "run $runs: G3 chain $chain_dir: $(jq -r .state "$chain_dir/chain_status.json" 2>/dev/null)${chain_stuck:+ (stuck)}"
	fi
	# gate progress is measured on indi_flight/GATE_STATUS.tsv, not on self-reported journal lines (owner, 2026-11-21)
	stale=$(cat "$LOG_DIR/gate_status.stale" 2>/dev/null || echo 0)
	if [ "$stale" -ge 2 ]; then
		prompt="$prompt
- indi_flight/GATE_STATUS.tsv has not changed for $stale sessions. Start with the route check (MISSION, \"Route
  check\"): name what blocks the next gate verdict, cut what does not lead to it, write the cut in STATE.md."
		log "run $runs: GATE_STATUS.tsv unchanged for $stale sessions, the orchestrator is told to run a route check"
	fi

	claude -p "$prompt" \
		--name "indi-orchestrator $ts" \
		--model "$MODEL" \
		--effort "$EFFORT" \
		--max-budget-usd "$budget" \
		--settings indi_flight/claude_settings.json \
		--tools "$TOOLS" \
		--strict-mcp-config \
		--exclude-dynamic-system-prompt-sections \
		--dangerously-skip-permissions \
		--output-format stream-json --verbose \
		> "$LOG_DIR/run-$ts.jsonl" 2> "$LOG_DIR/run-$ts.err" 9>&-
	rc=$?
	elapsed=$(($(date +%s) - start))
	result=$(jq -c 'select(.type=="result")' "$LOG_DIR/run-$ts.jsonl" 2>/dev/null | tail -1)
	subtype=$(jq -r '.subtype // "?"' <<<"$result" 2>/dev/null)
	cost=$(jq -r '.total_cost_usd // "?"' <<<"$result" 2>/dev/null)
	session=$(jq -r '.session_id // "?"' <<<"$result" 2>/dev/null)
	# context of the orchestrator's first and largest turn, to follow the token economy run by run
	ctx=$(jq -r 'select(.type=="assistant" and .parent_tool_use_id==null) | .message | "\(.id) \(.usage.input_tokens + .usage.cache_creation_input_tokens + .usage.cache_read_input_tokens)"' "$LOG_DIR/run-$ts.jsonl" 2>/dev/null |
		awk '!seen[$1]++ {n++; if (n == 1) f = $2; if ($2 > m) m = $2} END {if (n) printf "%dk start, %dk max, %d turns", f/1000, m/1000, n}')
	log "run $runs: exit $rc after ${elapsed}s, result $subtype, cost \$${cost:-?}, session $session, context ${ctx:-?}"
	calibrate_window "$LOG_DIR/run-$ts.jsonl" "${cost:-?}"
	calibrate_week "$LOG_DIR/run-$ts.jsonl" "${cost:-?}"
	# agent ledger written by the supervisor from the session log (the orchestrator no longer edits LEDGER.md)
	jq -r --arg ts "$ts" 'select(.type=="assistant" and .parent_tool_use_id==null) | .message.content[]? |
		select(.type=="tool_use" and (.name=="Agent" or .name=="Task")) |
		[$ts, (.input.model // "default"), (.input.subagent_type // "-"), (.input.description // "-")] | @tsv' \
		"$LOG_DIR/run-$ts.jsonl" >>"$LOG_DIR/agent_ledger.tsv" 2>/dev/null
	printf '%s\tSESSION\t%s\t%ss\t$%s\n' "$ts" "$subtype" "$elapsed" "${cost:-?}" >>"$LOG_DIR/agent_ledger.tsv"
	# gate status: count sessions in a row that left GATE_STATUS.tsv unchanged
	if [ -f indi_flight/GATE_STATUS.tsv ] && ! cmp -s indi_flight/GATE_STATUS.tsv "$LOG_DIR/gate_status.prev"; then
		echo 0 >"$LOG_DIR/gate_status.stale"
		log "run $runs: GATE_STATUS.tsv changed: $(diff "$LOG_DIR/gate_status.prev" indi_flight/GATE_STATUS.tsv 2>/dev/null | grep '^>' | cut -c3-120 | paste -sd';' | cut -c1-300)"
		cp indi_flight/GATE_STATUS.tsv "$LOG_DIR/gate_status.prev"
	else
		echo $(($(cat "$LOG_DIR/gate_status.stale" 2>/dev/null || echo 0) + 1)) >"$LOG_DIR/gate_status.stale"
	fi
	left=$(git status --porcelain --untracked-files=all -- indi_flight/results 2>/dev/null | wc -l)
	[ "$left" -eq 0 ] || log "run $runs: left $left dirty paths in indi_flight/results (next session is told to sort them)"

	# the usage gate at the top of the loop decides whether the next launch has room;
	# here only guard against a session that fails straight away for another reason
	if [ "$rc" -eq 0 ] || [ "$elapsed" -ge 300 ] || [ "$subtype" = "error_max_budget_usd" ]; then
		wait_s=60
	else
		wait_s=$LIMIT_WAIT
	fi

	{ [ -f indi_flight/DONE ] || [ -f indi_flight/STOP ]; } && break
	log "relaunching in ${wait_s}s (at $(date -d "@$(($(date +%s) + wait_s))" '+%F %T'))"
	wait_until $(($(date +%s) + wait_s))
done

if [ -f indi_flight/DONE ]; then
	log "orchestrator reported completion, see indi_flight/STATE.md"
else
	log "stopped by indi_flight/STOP"
fi
