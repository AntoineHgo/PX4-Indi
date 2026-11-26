#!/usr/bin/env bash
# G8 testable checks (GATES.md section 8). Run from repo root. Read-only.
set -u
F=indi_flight; R=$F/report; rc=0
res() { # name status detail
  echo "$2 $1${3:+: $3}"; [ "$2" = PASS ] || rc=1; }

# 1. evidence paths per gate row (GATE_STATUS.tsv column 3), relative to indi_flight/
miss=""
while IFS=$'\t' read -r item state ev _; do
  [ "$item" = item ] && continue
  e=$(printf '%s' "$ev" | sed -E 's/"[^"]*"//g')       # drop quoted section titles
  found=0
  IFS=';' read -ra parts <<<"$e"
  for p in "${parts[@]}"; do
    p=$(printf '%s' "$p" | sed -E 's/^[[:space:]]*(earlier:)?[[:space:]]*//')
    tok=${p%%[[:space:]]*}; rest=""
    [[ "$p" == *"("*")"* ]] && rest=$(printf '%s' "$p" | sed -E 's/^[^(]*\(([^)]*)\).*/\1/')
    if [[ "$tok" == */* || "$tok" == *.md ]]; then
      found=1; [ -e "$F/$tok" ] || miss="$miss $item:$F/$tok"
      last=""
      for sub in $(printf '%s' "$rest" | tr ',' ' '); do
        if [[ "$sub" == */* || "$sub" == *.md ]]; then
          # bare names may be shorthand for the previous sibling's subdirectory
          [ -e "$F/$tok/$sub" ] || [ -e "$F/$sub" ] || { [ -n "$last" ] && [ -e "$F/$tok/$last/$sub" ]; } || miss="$miss $item:$F/$tok/$sub"
          [[ "$sub" == */* ]] && last=${sub%/*}
        fi
      done
    fi
  done
  [ $found = 1 ] || miss="$miss $item:(no evidence path in column 3: '$ev')"
done < $F/GATE_STATUS.tsv
for g in 1 2 3 4 5 6 7 8; do
  grep -qE "^#+ .*(G$g\b|^#+ $g\. G$g)" $F/GATES.md || miss="$miss G$g:(no GATES.md heading)"
done
[ -z "$miss" ] && res "1 evidence paths exist" PASS || res "1 evidence paths exist" FAIL "$miss"

# 2. G1 evidence limits and G3 excluded corner listed in report/*.md
m=""
chk() { grep -qiE "$2" $R/*.md || m="$m [$1 /$2/]"; }
chk "G1 limit 1 holes" 'holes'
chk "G1 limit 2 Commander tick" 'Commander tick'
chk "G1 limit 3 EKF-truth height" 'A-14'
chk "G1 limit 4 EKF heading" 'A-19'
chk "G1 limit 5 bench params" 'SENS_BAR_AUTOCAL'
chk "G3 excluded corner (saturation-corner draws)" 'saturation[- ]corner|excluded corner'
chk "G3 class (b) beyond-range physics" 'beyond-range'
[ -z "$m" ] && res "2 G1 limits and G3 excluded corners listed" PASS || res "2 G1 limits and G3 excluded corners listed" FAIL "missing in $R/*.md:$m"

# 3, 4 files
[ -s $R/06_bringup_checklist.md ] && res "3 bring-up checklist" PASS || res "3 bring-up checklist" FAIL "$R/06_bringup_checklist.md"
m=""; for f in $R/A_history_errata.md $F/results/errata.md; do [ -s $f ] || m="$m $f"; done
[ -z "$m" ] && res "4 errata and history appendix" PASS || res "4 errata and history appendix" FAIL "$m"

# 5. translations untouched vs main
d=$(git diff --stat main -- docs/ko docs/zh docs/uk 2>&1)
[ -z "$d" ] && res "5 docs/ko zh uk diff vs main empty" PASS || res "5 docs/ko zh uk diff vs main empty" FAIL "$(printf '%s' "$d" | tail -3 | tr '\n' '|')"

# 6. page in docs/en only
o=$(find docs -ipath '*indi*' -not -path 'docs/en/*' -type f 2>/dev/null | grep -viE '\.(jpg|jpeg|png|svg|gif)$' | tr '\n' ' ')
if [ -f docs/en/config_mc/indi_control.md ] && [ -z "$o" ]; then res "6 user page in docs/en only" PASS
else res "6 user page in docs/en only" FAIL "en page $( [ -f docs/en/config_mc/indi_control.md ] && echo present || echo MISSING); elsewhere: $o"; fi

# 7. markdown lint only if a docs target exists
if grep -qE '^[a-zA-Z_-]*(docs|lint)[a-zA-Z_-]*:' Makefile && grep -qE '^(docs|markdown|lint_docs|check_docs|docs_lint)[a-zA-Z_-]*:' Makefile; then
  res "7 markdown lint" FAIL "docs target exists; run it manually (not run by this script)"
else res "7 markdown lint" PASS "not applicable: no docs target (only msg_docs generator)"; fi
exit $rc
