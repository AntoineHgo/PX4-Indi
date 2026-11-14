# Report-only image (D-pdf): pandoc + XeLaTeX to build the report PDF.
# Kept separate from px4-indi-sim so the simulation image, and every
# benchmark result produced with it, stays unchanged.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
	pandoc texlive-xetex texlive-latex-recommended texlive-fonts-recommended \
	lmodern fonts-dejavu-core \
	&& rm -rf /var/lib/apt/lists/*
