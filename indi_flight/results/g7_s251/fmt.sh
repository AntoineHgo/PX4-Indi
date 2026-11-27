#!/usr/bin/env bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
indi_project/docker/run.sh -n s251_fmt -t 600 -- bash -c 'n=0; bad=0; for f in "$@"; do n=$((n+1)); out=$(Tools/astyle/fix_code_style.sh --dry-run --formatted "$f" 2>&1); [ -n "$out" ] && { bad=$((bad+1)); echo "$out" | head -5; }; done; echo "checked=$n reported=$bad"' _ "$@"
