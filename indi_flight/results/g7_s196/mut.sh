#!/usr/bin/env bash
# usage: mut.sh <file> <line> <sed-s-expr|-> <ctest-regex>   host-side edit, docker build+test, revert
cd "$(dirname "$0")/../../.."
f=$1; l=$2; e=$3; flt=$4
if [ "$e" != "-" ]; then
  sed -i "${l}${e}" "$f"; git diff -U0 -- "$f" | grep '^[-+][^-+]'
fi
indi_project/docker/run.sh -- bash -c "make tests TESTFILTER=\"'$flt'\" 2>&1 | grep -E 'FAILED|Failed|tests passed|tests failed|rror:' | sort -u | head -15" 
git checkout -- "$f"
