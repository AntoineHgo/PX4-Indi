#!/usr/bin/env bash
# Builds the px4-indi-sim image used for every build and simulation of the INDI project.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(cd "${SCRIPT_DIR}/../.." && pwd)

docker build \
	--tag px4-indi-sim \
	--build-arg USER_ID="$(id -u)" \
	--build-arg GROUP_ID="$(id -g)" \
	--file "${SCRIPT_DIR}/Dockerfile" \
	"${REPO_DIR}/Tools/setup"
