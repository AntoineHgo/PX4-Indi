#!/usr/bin/env bash
# Relaunches the orchestrator until it creates indi_project/DONE.
# Each launch is a fresh session that resumes from indi_project/STATE.md.
# Stop it gracefully with: touch indi_project/STOP
set -u
cd "$(dirname "$0")/.."
REPO=$PWD

PROMPT_FILE=indi_project/ORCHESTRATOR_PROMPT.md
GUARD=indi_project/guard.sh
LOG_DIR=indi_project/logs
MODEL="${MODEL:-claude-fable-5-2}"
EFFORT="${EFFORT:-xhigh}"
BRANCH="${BRANCH:-feat/indi-control}"
EXPECTED_ORIGIN="${EXPECTED_ORIGIN:-AntoineHgo/PX4-Indi}"
LIMIT_WAIT="${LIMIT_WAIT:-1800}"   # seconds to wait after a failed or very short run (usage limit, network, ...)
MAX_RUNS="${MAX_RUNS:-300}"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG_DIR/supervisor.log"; }
die() { log "ABORT: $*"; exit 1; }

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
log "preflight ok: branch $BRANCH, model $MODEL, effort $EFFORT"

# --- supervise ---
runs=0
while [ ! -f indi_project/DONE ] && [ ! -f indi_project/STOP ]; do
	runs=$((runs + 1))
	[ "$runs" -le "$MAX_RUNS" ] || die "reached MAX_RUNS=$MAX_RUNS"
	ts=$(date +%Y%m%d-%H%M%S)
	start=$(date +%s)
	log "run $runs: launching orchestrator (log: $LOG_DIR/run-$ts.jsonl)"

	claude -p "$(cat "$PROMPT_FILE")" \
		--name "indi-orchestrator $ts" \
		--model "$MODEL" \
		--effort "$EFFORT" \
		--settings indi_project/claude_settings.json \
		--dangerously-skip-permissions \
		--output-format stream-json --verbose \
		> "$LOG_DIR/run-$ts.jsonl" 2> "$LOG_DIR/run-$ts.err" 9>&-
	rc=$?
	elapsed=$(($(date +%s) - start))
	result=$(jq -c 'select(.type=="result")' "$LOG_DIR/run-$ts.jsonl" 2>/dev/null | tail -1)
	cost=$(jq -r '.total_cost_usd // "?"' <<<"$result" 2>/dev/null)
	log "run $runs: exit $rc after ${elapsed}s, cost \$${cost:-?}"

	if [ "$rc" -eq 0 ] && [ "$elapsed" -ge 300 ]; then
		wait_s=60
	else
		wait_s=$LIMIT_WAIT
	fi

	# usage limit: sleep until the reset time the API reports, plus a margin
	if [ "$(jq -r '.api_error // empty' <<<"$result" 2>/dev/null)" = "usage_limit_reached" ]; then
		msg=$(jq -r '.result // empty' <<<"$result")
		log "usage limit: $msg"
		grep -qi "spend limit" <<<"$msg" && log "WARNING: a spend limit is reached, relaunches will keep failing until it is raised"
		reset=$(grep -oiE 'resets [^(·]+' <<<"$msg" | head -1 | sed -E 's/^resets //I; s/,//g; s/[[:space:]]+$//')
		if reset_at=$(date -d "$reset" +%s 2>/dev/null); then
			[ "$reset_at" -le "$(date +%s)" ] && reset_at=$((reset_at + 86400))
			wait_s=$((reset_at - $(date +%s) + 120))
		fi
	fi

	{ [ -f indi_project/DONE ] || [ -f indi_project/STOP ]; } && break
	log "relaunching in ${wait_s}s (at $(date -d "@$(($(date +%s) + wait_s))" '+%F %T'))"
	sleep "$wait_s" 9>&-
done

if [ -f indi_project/DONE ]; then
	log "orchestrator reported completion, see indi_project/STATE.md"
else
	log "stopped by indi_project/STOP"
fi
