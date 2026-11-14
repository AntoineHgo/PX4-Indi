# Bibliography

Every source below was opened and read for this work; a note written from its text is kept under
`indi_project/research/notes/`. Citation keys in the chapters (e.g. [smeur2016]) refer to the entries below.

## Published works

- **[acquatella2017]** P. Acquatella B., W. van Ekeren, Q.P. Chu, "PI(D) tuning for Flight Control Systems via Incremental Nonlinear Dynamic Inversion", arXiv:1701.08981v3, 2017. https://arxiv.org/abs/1701.08981. Reading note: `research/notes/acquatella2017.md`.
- **[blaha2024]** T.M. Blaha, E.J.J. Smeur, B.D.W. Remes, "Control of Unknown Quadrotors from a Single Throw", IROS 2024, arXiv:2406.11723v3. https://arxiv.org/abs/2406.11723. Reading note: `research/notes/blaha2024.md`.
- **[smeur2016]** E.J.J. Smeur, Q.P. Chu, G.C.H.E. de Croon, "Adaptive Incremental Nonlinear Dynamic Inversion for Attitude Control of Micro Air Vehicles", J. Guidance, Control, and Dynamics 39(3), 2016, doi:10.2514/1.G001490. https://doi.org/10.2514/1.G001490. Reading note: `research/notes/smeur2016.md`.
- **[smeur2018]** E.J.J. Smeur, G.C.H.E. de Croon, Q.P. Chu, "Cascaded Incremental Nonlinear Dynamic Inversion for MAV Disturbance Rejection", Control Engineering Practice, 2018, arXiv:1701.07254. https://arxiv.org/abs/1701.07254. Reading note: `research/notes/smeur2018.md`.
- **[steffensen2023]** R. Steffensen, A. Steinert, E.J.J. Smeur, "Nonlinear Dynamic Inversion with Actuator Dynamics: an Incremental Control Perspective", J. Guidance, Control, and Dynamics, 2023. https://arxiv.org/abs/2201.09805 (copy read: arXiv v2, 25 Nov 2022, `raw/robustness/steffensen_arxiv.pdf`). Reading note: `research/notes/steffensen2023.md`.
- **[tal2021]** E. Tal, S. Karaman, "Accurate Tracking of Aggressive Quadrotor Trajectories using Incremental Nonlinear Dynamic Inversion and Differential Flatness", IEEE Trans. Control Syst. Technol., 2021 (venue per task brief, not confirmed in text read); arXiv:1809.04048v2. https://arxiv.org/pdf/1809.04048. Reading note: `research/notes/tal2021.md`.
- **[wang2019]** X. Wang, E.-J. van Kampen, Q.P. Chu, P. Lu, "Stability Analysis for Incremental Nonlinear Dynamic Inversion Control", J. Guidance, Control, and Dynamics 42(5), 2019, doi:10.2514/1.G003791. https://doi.org/10.2514/1.G003791 (copy read: TU Delft repository green open-access PDF, `raw/robustness/wang_pure.pdf`). Reading note: `research/notes/wang2019.md`.

## Open-source implementations and prior PX4 work

- **[impl_paparazzi]** Paparazzi UAV, `sw/airborne/firmwares/rotorcraft/stabilization/stabilization_indi{,_simple}.c`, commit c04ffe40a035b997dc71e7d7965cbddb07606695. https://github.com/paparazzi/paparazzi. Reading note: `research/notes/impl_paparazzi.md`.
- **[impl_px4_prior]** PX4 PRs #25216 (closed WIP MC INDI), #25166 (FW iNDI), #25863/#25864, forum threads 10953/36293, and lei-ss/indi (Paparazzi simple INDI ported to PX4). https://github.com/PX4/PX4-Autopilot/pull/25216 , https://github.com/lei-ss/indi. Reading note: `research/notes/impl_px4_prior.md`.

## Project-internal documents

- **[review_s16]** Independent review of the INDI control law and its PX4 integration, carried out during this project (sessions 16-21), with findings triaged into fixes and report limitations. `indi_project/review/control_law_review_s16.md`.
