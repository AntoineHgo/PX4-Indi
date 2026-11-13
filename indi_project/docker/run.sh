#!/usr/bin/env bash
# Non-interactive counterpart of Tools/docker_run.sh for the INDI project.
#
# Runs a command in the px4-indi-sim image as the host user, with the
# repository mounted at its own path and ~/.ccache shared. No TTY, no
# privileged options, no published ports, and a wall-clock timeout.
#
# Usage: indi_project/docker/run.sh [options] -- <command> [args...]
#        indi_project/docker/run.sh [options] '<shell command line>'
#   -n NAME      container name suffix (container is px4-indi-NAME), default: pid
#   -t SECONDS   wall-clock timeout, default 3600
#   -c CPUS      CPU limit (docker --cpus), default: unlimited
#   -e VAR=VAL   extra environment variable (repeatable)
#   -N           give the container its own network namespace with no external
#                access (loopback only)
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(cd "${SCRIPT_DIR}/../.." && pwd)
IMAGE=${PX4_INDI_IMAGE:-px4-indi-sim}

NAME=$$
TIMEOUT_S=3600
DOCKER_ARGS=()

while getopts "n:t:c:e:N" opt; do
	case "$opt" in
	n) NAME=$OPTARG ;;
	t) TIMEOUT_S=$OPTARG ;;
	c) DOCKER_ARGS+=(--cpus "$OPTARG") ;;
	e) DOCKER_ARGS+=(--env "$OPTARG") ;;
	N) DOCKER_ARGS+=(--network none) ;;
	*) exit 64 ;;
	esac
done
shift $((OPTIND - 1))
[ "${1:-}" = "--" ] && shift
[ $# -ge 1 ] || { echo "usage: $0 [options] -- <command>" >&2; exit 64; }

CCACHE_DIR=${HOME}/.ccache
mkdir -p "${CCACHE_DIR}"

# a single argument is a shell command line, several are an argv
if [ $# -eq 1 ]; then
	set -- /bin/bash -c "$1"
fi

exec docker run --rm --init \
	--name "px4-indi-${NAME}" \
	--workdir "${REPO_DIR}" \
	--user "$(id -u):$(id -g)" \
	--env CCACHE_DIR="${CCACHE_DIR}" \
	--env PX4_INDI_REPO="${REPO_DIR}" \
	--volume "${CCACHE_DIR}:${CCACHE_DIR}:rw" \
	--volume "${REPO_DIR}:${REPO_DIR}:rw" \
	--stop-timeout 10 \
	"${DOCKER_ARGS[@]}" \
	"${IMAGE}" \
	timeout --signal=TERM --kill-after=15 "${TIMEOUT_S}" "$@"
