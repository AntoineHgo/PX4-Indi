#!/usr/bin/env bash
# Builds indi_project/report/report.pdf from the chapter Markdown files in the
# px4-indi-report image (built from report.Dockerfile, D-pdf).
# Usage: indi_project/docker/build_report.sh
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPORT_DIR=$(cd "${SCRIPT_DIR}/../report" && pwd)
PX4_INDI_IMAGE=px4-indi-report exec "${SCRIPT_DIR}/run.sh" -n report -t 600 -N \
	"cd '${REPORT_DIR}' && pandoc [01][0-9]_*.md -o report.pdf --pdf-engine=xelatex \
	--resource-path=. --toc -V geometry:margin=25mm \
	-V mainfont='DejaVu Serif' -V monofont='DejaVu Sans Mono' -V colorlinks=true \
	--metadata title='INDI rate control for multicopters in PX4'"
