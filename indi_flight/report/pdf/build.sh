#!/usr/bin/env bash
# Build the INDI report: optional figure step, then latexmk (lualatex), then copy the PDF.
# Usage: build.sh [--no-figs]
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # indi_flight/report/pdf
root="$(cd "$here/../.." && pwd)"                          # indi_flight

make_figs=1
for arg in "$@"; do
  case "$arg" in
    --no-figs) make_figs=0 ;;
    -h|--help) echo "usage: $0 [--no-figs]"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [[ $make_figs -eq 1 && -f "$root/bench/report_figs/make_all.sh" ]]; then
  echo "== figures =="
  bash "$root/bench/report_figs/make_all.sh"
else
  echo "== figures skipped =="
fi

echo "== latexmk =="
mkdir -p "$here/build/chapters"
cd "$here"
latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex

cp "$here/build/main.pdf" "$here/indi_report.pdf"
echo "== done: $here/indi_report.pdf =="
