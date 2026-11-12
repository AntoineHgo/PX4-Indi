#!/usr/bin/env bash
# PreToolUse hook for the unattended INDI orchestrator (see claude_settings.json).
# Reads the tool call as JSON on stdin; exit 2 blocks the call and returns the
# message on stderr to the agent. Best-effort pattern matching, not a sandbox.

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PUSH_BRANCH_FORBIDDEN='main'

deny() {
	echo "BLOCKED by indi_project/guard.sh: $1. Stay inside the project boundaries and do not try to work around this guard." >&2
	exit 2
}

command -v jq >/dev/null || deny "jq is missing, the guard cannot inspect tool calls"

input=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$input")
cwd=$(jq -r '.cwd // empty' <<<"$input")
[ -n "$cwd" ] || cwd=$REPO

# 0 if the resolved path is somewhere the agent may write or delete
path_allowed() {
	local p
	p=$(cd "$cwd" 2>/dev/null && realpath -m -- "$1") || return 1

	case "$p" in
	"$REPO"/.git | "$REPO"/.git/* | "$REPO"/indi_project) return 1 ;;
	"$REPO"/indi_project/guard.sh | "$REPO"/indi_project/claude_settings.json) return 1 ;;
	"$REPO"/indi_project/run_orchestrator.sh | "$REPO"/indi_project/ORCHESTRATOR_PROMPT.md) return 1 ;;
	"$REPO"/* | /tmp/* | "$HOME"/.claude/projects/*) return 0 ;;
	*) return 1 ;;
	esac
}

has() { grep -Eq -- "$1" <<<"$cmd"; }

case "$tool" in
Edit | Write | NotebookEdit)
	p=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' <<<"$input")
	[ -n "$p" ] || deny "no file path in the tool call"
	path_allowed "$p" || deny "'$p' is outside the repository or is a protected file"
	;;

Bash)
	cmd=$(jq -r '.tool_input.command // empty' <<<"$input")

	# privilege, system and shell-environment changes
	has '(^|[^[:alnum:]_./-])(sudo|doas|pkexec)([[:space:]]|$)' && deny "no privilege escalation"
	has '(^|[^[:alnum:]_./-])(shutdown|reboot|poweroff|halt|mkfs[.[:alnum:]]*|fdisk|parted|crontab|systemctl|apt|apt-get|snap|dpkg)([[:space:]]|$)' && deny "no system administration commands on the host"
	has '(^|[^[:alnum:]_./-])dd[[:space:]]+[^;|&]*of=/dev/' && deny "no raw device writes"
	has '(curl|wget)[^;&]*\|[[:space:]]*(ba|z|da)?sh' && deny "no piping downloads into a shell"
	has '(\.ssh|\.gnupg|\.gitconfig|\.bashrc|\.zshrc|\.zshenv|\.profile|\.claude/settings|\.claude\.json|\.config/gh)' && deny "no access to credentials or shell/tool configuration"
	# supervisor files and git hooks may be read, never modified
	while IFS= read -r seg; do
		grep -Eq '(guard\.sh|claude_settings\.json|run_orchestrator\.sh|ORCHESTRATOR_PROMPT\.md|\.git/hooks)' <<<"$seg" || continue
		grep -Eq '(>|(^|[^[:alnum:]_.-])(tee|mv|cp|rm|ln|chmod|chown|truncate|install|dd|patch)([[:space:]]|$)|(sed|perl)[[:space:]]+[^;|&]*-[[:alnum:]]*i|git[[:space:]]+(checkout|restore|rm|mv|apply|stash)|open\(|write)' <<<"$seg" &&
			deny "supervisor files and git hooks may be read but not modified"
	done < <(tr ';|&\n' '\n\n\n\n' <<<"$cmd")
	has '(^|[^[:alnum:]_./-])claude[[:space:]]+[^;|&]*(-p|--print|--dangerously|--permission-mode|--settings)' && deny "no nested claude sessions, use the Agent tool"
	has 'pip3?[[:space:]]+install[^;|&]*--break-system-packages' && deny "install Python packages in a venv inside the repo or in the container image"

	# git: pushes go to origin, on a project branch, as fast-forwards
	if has '(^|[^[:alnum:]_./-])git[[:space:]]'; then
		has 'git[[:space:]]+([^;|&]*[[:space:]])?(clean|filter-branch|filter-repo|gc|reflog[[:space:]]+expire)([[:space:]]|$)' && deny "this would destroy untracked project files or history (remove build output by path instead)"
		has 'git[[:space:]]+([^;|&]*[[:space:]])?remote[[:space:]]+(add|remove|rm|rename|set-url)' && deny "remotes are fixed"
		has 'git[[:space:]]+([^;|&]*[[:space:]])?config[[:space:]]+[^;|&]*--(global|system)' && deny "no global git configuration"
		has 'git[[:space:]]+([^;|&]*[[:space:]])?(branch[[:space:]]+[^;|&]*-[dDmM]|checkout[[:space:]]+[^;|&]*-B|reset[[:space:]]+[^;|&]*--hard)[^;|&]*[[:space:]]'"$PUSH_BRANCH_FORBIDDEN"'([[:space:]]|$)' && deny "leave the $PUSH_BRANCH_FORBIDDEN branch alone"

		if has 'git[[:space:]]+([^;|&]*[[:space:]])?push([[:space:]]|$)'; then
			push=$(grep -Eo -- 'git[[:space:]]+([^;|&]*[[:space:]])?push([[:space:]][^;|&]*|$)' <<<"$cmd")
			phas() { grep -Eq -- "$1" <<<"$push"; }
			phas '(--force|--mirror|--delete|--all|--tags|--prune|--no-verify|[[:space:]]-[[:alnum:]]*[fd][[:alnum:]]*([[:space:]]|$)|[[:space:]]\+|[[:space:]]:)' && deny "plain fast-forward pushes only (no force, delete, mirror, --all, --no-verify)"
			phas '(upstream|://|@)' && deny "push only to the 'origin' remote, by name"
			phas 'push[[:space:]]+([^;|&]*[[:space:]])?origin([[:space:]]|$)' || deny "name the remote and branch explicitly: git push origin <project-branch>"
			phas '(^|[[:space:]:/])'"$PUSH_BRANCH_FORBIDDEN"'([[:space:]]|$)' && deny "do not push to $PUSH_BRANCH_FORBIDDEN, push the project branch"
			[ "$(git -C "$cwd" branch --show-current 2>/dev/null)" = "$PUSH_BRANCH_FORBIDDEN" ] && deny "you are on $PUSH_BRANCH_FORBIDDEN, switch to the project branch before pushing"
		fi
	fi

	has '(^|[^[:alnum:]_./-])make[[:space:]]+[^;|&]*distclean' && deny "distclean runs git clean and would delete untracked project files (remove build directories by path instead)"
	has '(^|[^[:alnum:]_./-])gh[[:space:]]+(repo[[:space:]]+(delete|edit|rename|archive|create|fork)|pr[[:space:]]+(create|merge|close|edit|comment|review)|issue[[:space:]]+(create|close|edit|comment)|release|secret|variable|auth|ssh-key|gpg-key|workflow[[:space:]]+run|api[[:space:]][^;|&]*(-X|--method|-f|-F|--field|--input))' && deny "GitHub is read-only apart from git push"

	# recursive deletes: every target must be a literal path inside the repo or /tmp
	while IFS= read -r seg; do
		grep -Eq '(^|[^[:alnum:]_./-])rm[[:space:]]' <<<"$seg" || continue
		grep -Eq '[[:space:]](-[[:alnum:]]*[rR][[:alnum:]]*|--recursive)([[:space:]]|$)' <<<"$seg" || continue
		grep -Eq '[$`~]|\.\.' <<<"$seg" && deny "recursive rm needs literal paths without variables, ~ or '..'"
		grep -Eq '(^|[[:space:]])cd[[:space:]]' <<<"$cmd" && deny "do not combine cd with a recursive rm, use absolute paths"

		targets=${seg#*rm }
		for tok in $targets; do
			tok=${tok//[\"\']/}
			case "$tok" in -* | '') continue ;; esac
			path_allowed "$tok" || deny "recursive rm target '$tok' is outside the repository or protected"
		done
	done < <(tr ';|&\n' '\n\n\n\n' <<<"$cmd")

	# docker: no host-level access, mounts limited to the repo, ccache and /tmp
	if has '(^|[^[:alnum:]_./-])docker([[:space:]]|$)'; then
		has '(--privileged|--pid[= ]+host|--ipc[= ]+host|--userns[= ]+host|--cap-add|--device|--security-opt|docker\.sock|--mount)' && deny "no privileged or host-level container options (bind mounts go through -v)"
		has 'docker[[:space:]]+((system|volume|image|container|builder|network)[[:space:]]+(prune|rm)|push|login|logout|swarm|context|plugin)' && deny "no docker prune, push or daemon-level commands"

		if has 'docker[[:space:]]+(rmi|image[[:space:]]+rm)'; then
			for tok in $(grep -Eo -- 'docker[[:space:]]+(rmi|image[[:space:]]+rm)[^;|&]*' <<<"$cmd" | sed -E 's/docker[[:space:]]+(rmi|image[[:space:]]+rm)//'); do
				case "$tok" in -* | px4-indi-*) ;; *) deny "only px4-indi-* images may be removed" ;; esac
			done
		fi

		while IFS= read -r src; do
			[ -n "$src" ] || continue
			grep -Eq '[$`~]' <<<"$src" && deny "docker volume sources must be literal absolute paths (got '$src')"
			case "$(realpath -m -- "$src")" in
			"$REPO" | "$REPO"/* | "$HOME"/.ccache | "$HOME"/.ccache/* | /tmp/*) ;;
			*) deny "docker may only mount the repository, ~/.ccache (as a literal path) or /tmp (got '$src')" ;;
			esac
		done < <(grep -Eo -- '(-v|--volume)[= ]+[^[:space:]]+' <<<"$cmd" | sed -E "s/^(-v|--volume)[= ]+//; s/[\"']//g; s/:.*//")
	fi
	;;
esac

exit 0
