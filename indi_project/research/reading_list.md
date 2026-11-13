# Phase 1 reading list (bounded)

Rule: one note per entry in `research/notes/<id>.md`, written by whoever reads
the source, with section/page/line references for every claim. A source is
added later only when the design or a surprising result needs it. Status is
updated in `STATE.md`, not here.

Local copies live in `research/raw/` (gitignored). `raw` paths below are
relative to `research/raw/`.

## Core papers (8 + 1 background)

| id | Source | Why it is on the list | Local copy |
|----|--------|-----------------------|------------|
| smeur2016 | Smeur, Chu, de Croon, "Adaptive Incremental Nonlinear Dynamic Inversion for Attitude Control of Micro Air Vehicles", JGCD 39(3), 2016, doi:10.2514/1.G001490 | Reference derivation of rate-loop INDI for multirotors, synchronised filtering of gyro and actuator state, first-order actuator model, adaptive (LMS) effectiveness | `foundations/inaoep_14032018.txt` |
| smeur2018 | Smeur, de Croon, Chu, "Cascaded incremental nonlinear dynamic inversion for MAV disturbance rejection", CEP 2018, arXiv:1701.07254 | Outer-loop (linear acceleration) INDI, thrust/attitude increments, wind gust results | `foundations/smeur2018_cascaded.txt` |
| sieberling2010 | Sieberling, Chu, Mulder, "Robust Flight Control Using Incremental Nonlinear Dynamic Inversion and Angular Acceleration Prediction", JGCD 33(6), 2010, doi:10.2514/1.49978 | Robustness of INDI to model mismatch, effect of angular-acceleration estimation delay, prediction | to fetch |
| wang2019 | Wang, van Kampen, Chu, Lu, "Stability Analysis for Incremental Nonlinear Dynamic Inversion Control", JGCD 42(5), 2019 | Formal robustness/stability results, effect of sampling and delay | `robustness/wang_pure.pdf` |
| steffensen2023 | Steffensen, Steinert, Smeur, "Nonlinear Dynamic Inversion with Actuator Dynamics: An Incremental Control Perspective", JGCD 2023 | Actuator dynamics as part of the inversion, relation NDI/INDI | `robustness/steffensen_arxiv.pdf` |
| tal2021 | Tal, Karaman, "Accurate Tracking of Aggressive Quadrotor Trajectories Using Incremental Nonlinear Dynamic Inversion and Differential Flatness", IEEE TCST 2021, arXiv:1809.04048 | Full INDI cascade with motor-speed feedback, aggressive tracking evidence | to fetch |
| sun2022 | Sun, Romero, Foehn, Kaufmann, Scaramuzza, "A Comparative Study of Nonlinear MPC and Differential-Flatness-Based Control for Quadrotor Agile Flight", IEEE T-RO 2022, arXiv:2109.01365 | Independent comparison, role of the INDI inner loop in robustness to model mismatch | to fetch |
| blaha2024 | Blaha, Smeur, Remes, "Control of Unknown Quadrotors from a Single Throw", IROS 2024, arXiv:2406.11723 | Online effectiveness/actuator identification, INDI in Betaflight-derived firmware (indiflight) | `papers_dl/blaha_iros.txt` |
| acquatella2017 (background) | Acquatella B., van Ekeren, Chu, "PI(D) tuning for Flight Control Systems via Incremental Nonlinear Dynamic Inversion", arXiv:1701.08981 (venue not stated in the text) | Equivalence between INDI and PI(D) with specific gains: essential for an honest INDI-vs-PID comparison | `foundations/arxiv_1701.08981.txt` |

Further on disk, read only if needed: Bacon & Ostroff 2000 (`foundations/bacon2000.txt`, origin of the incremental form), Smeur et al. tailsitter (`foundations/arxiv_1802.00714.txt`), Smeur IMAV 2017 (`foundations/smeur2017_imav.txt`), Blaha IMAV 2024 (`papers_dl/imav2024.txt`), Politecnico thesis (`papers_dl/polito.txt`).

## Reference implementations (3) and PX4 ecosystem

| id | Code | What to extract | Local copy |
|----|------|-----------------|------------|
| impl_paparazzi | Paparazzi `stabilization_indi_simple.c` and `stabilization_indi.c` | Filter structure, actuator model, effectiveness adaptation, saturation/WLS, arming/landing handling | `paparazzi/` |
| impl_indiflight | indiflight (Betaflight fork, TU Delft) | Rate INDI with motor-speed (DShot telemetry) feedback, allocation, onboard identification | `indiflight/`, `indiflightSupport/`, `activeset/` |
| impl_px4_prior | lei-ss/indi (Paparazzi simple INDI ported to PX4 attitude) and PX4 PRs #25216 (closed WIP INDI), #25166 (fixed-wing iNDI), #25863/#25864 | Prior PX4 integration choices, why they did not land | `leiss_indi_master/`, `px4_eco/` |
| (optional) impl_crazyflie | Crazyflie `controller_indi.c` | Second small-MAV implementation for cross-check | `crazyflie/` |
