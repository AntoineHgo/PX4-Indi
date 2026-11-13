#!/usr/bin/env bash
# Follows the latest orchestrator run live, one line per event.
# Usage: indi_project/watch.sh [run-log.jsonl]     (Ctrl-C to quit, the run is not affected)
[ -n "${1:-}" ] && f=$(realpath -- "$1")
cd "$(dirname "$0")/logs" || exit 1
f=${f:-$(ls -t run-*.jsonl 2>/dev/null | head -1)}
[ -n "$f" ] || { echo "no run log yet" >&2; exit 1; }
echo "following $f"
tail -n +1 -F "$f" | jq --unbuffered -r '
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
	else empty end'
