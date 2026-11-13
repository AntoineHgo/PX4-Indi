#!/usr/bin/env bash
# Follows the orchestrator live, one line per event, across relaunches: when the supervisor
# starts a new run it switches to the new run log, and supervisor lines (launches, waits for a
# usage reset) are shown as SUP lines in between.
# Usage: indi_project/watch.sh [run-log.jsonl]   (with a file: follow only that run)
# Ctrl-C to quit, the orchestrator is not affected.
set -u
pinned=
[ -n "${1:-}" ] && pinned=$(realpath -- "$1")
cd "$(dirname "$0")/logs" || exit 1

# fromjson? skips a partial or corrupt line (a run cut off mid-write) instead of killing jq
read -r -d '' FILTER <<'EOF'
fromjson? |
(if .parent_tool_use_id then "  [sub " + .parent_tool_use_id[-5:] + "] " else "" end) as $who |
if .type == "assistant" then
	.message.content[]? |
	if .type == "text" then $who + "SAY  " + (.text | gsub("\n"; " ") | .[0:300])
	elif .type == "tool_use" then $who + "TOOL " + .name + " " +
		((.input.description // .input.command // .input.file_path // .input.query // .input.url // (.input | tostring)) | tostring | gsub("\n"; " ") | .[0:200])
	else empty end
elif .type == "system" and (.subtype == "task_started" or .subtype == "task_notification") and (.owned_by_subagent | not) then
	"TASK " + .subtype + " " + (.description // .summary // "" | .[0:200]) + " " + (.status // "")
elif .type == "rate_limit_event" then
	"USAGE " + ([.rate_limit_info.unifiedWindows // {} | to_entries[] | "\(.key)=\(.value.utilization)"] | join(" "))
elif .type == "result" then
	"RESULT " + (.subtype // "") + " $" + ((.total_cost_usd // 0) * 100 | round / 100 | tostring) + " " + (.result // "" | .[0:300])
else empty end
EOF

run_pid=
sup_pid=
cleanup() {
	trap - EXIT
	kill $run_pid $sup_pid 2>/dev/null
	exit 0
}
trap cleanup INT TERM EXIT

if [ -z "$pinned" ]; then
	tail -n 3 -F supervisor.log 2>/dev/null > >(sed -u 's/^/SUP  /') &
	sup_pid=$!
fi

current=
while :; do
	f=${pinned:-$(ls -t run-*.jsonl 2>/dev/null | head -1)}
	if [ -n "$f" ] && [ "$f" != "$current" ]; then
		[ -n "$run_pid" ] && kill "$run_pid" 2>/dev/null
		echo "=== following $f"
		# killing tail closes jq's input, so jq exits with it
		tail -n +1 -F -- "$f" 2>/dev/null > >(jq --unbuffered -Rr "$FILTER") &
		run_pid=$!
		current=$f
	fi
	sleep 5 &
	wait $! # interruptible, so Ctrl-C or kill cleans up at once
done
