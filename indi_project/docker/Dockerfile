# Build and simulation environment for the INDI project (see indi_project/).
#
# Reuses the repository's own setup script with the simulation tools included
# (the stock Tools/setup/Dockerfile passes --no-sim-tools, so it has no Gazebo).
# The build context is Tools/setup, see indi_project/docker/build.sh.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=UTC
ENV RUNS_IN_DOCKER=true

# PX4 build dependencies, Gazebo Harmonic, MAVSDK and pytest (test-requirements.txt).
# SITL only: no NuttX toolchain.
COPY requirements.txt test-requirements.txt ubuntu.sh /tmp/px4-setup/
RUN bash /tmp/px4-setup/ubuntu.sh --no-nuttx \
	&& rm -rf /var/lib/apt/lists/*

# Benchmark harness extras: software GL for a headless Gazebo server, process
# tools for run supervision, scipy for the analysis scripts.
RUN apt-get update -y --quiet \
	&& apt-get install -y --quiet --no-install-recommends \
		libgl1-mesa-dri \
		procps \
		xvfb \
	&& rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --break-system-packages scipy

# The repository is bind-mounted and owned by the host user
RUN git config --system --add safe.directory '*'

# Same uid/gid as the host user, so files written to the repository stay theirs
ARG USER_ID=1001
ARG GROUP_ID=1001
RUN if ! getent group "${GROUP_ID}" > /dev/null; then groupadd -g "${GROUP_ID}" px4; fi \
	&& if getent passwd "${USER_ID}" > /dev/null; then userdel -r "$(getent passwd "${USER_ID}" | cut -d: -f1)"; fi \
	&& useradd --shell /bin/bash -u "${USER_ID}" -g "${GROUP_ID}" -m px4

USER ${USER_ID}:${GROUP_ID}
ENV HOME=/home/px4

CMD ["/bin/bash"]
