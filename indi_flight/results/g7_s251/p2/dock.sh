#!/bin/bash
# usage: dock.sh script.sh   (px4-indi-sim; worktree + repo .git read-only for worktree gitdir)
docker run --rm --init --user "$(id -u):$(id -g)" --env HOME=/tmp --env GIT_SUBMODULES_ARE_EVIL=1 \
 --volume /tmp/indi_fwbranch_s251:/tmp/indi_fwbranch_s251:rw \
 --volume /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g7_s251:/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g7_s251:rw \
 --volume /home/ahugo/Documents/Drotek/Codes/PX4-Indi/.git:/home/ahugo/Documents/Drotek/Codes/PX4-Indi/.git:ro \
 --volume /home/ahugo/Documents/Drotek/Codes/PX4-Indi/src/modules/mavlink/mavlink:/home/ahugo/Documents/Drotek/Codes/PX4-Indi/src/modules/mavlink/mavlink:ro \
 --workdir /tmp/indi_fwbranch_s251 px4-indi-sim:latest timeout 3500 bash "$1"
