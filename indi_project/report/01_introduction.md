# 1 Introduction

## 1.1 Motivation

The multicopter flight controller in PX4 is a cascade. A position loop feeds an attitude loop, and the attitude loop feeds an angular-rate loop that produces the torque commands passed to control allocation. The attitude loop is a proportional controller. The rate loop is a PID controller (chapter 4). This structure is widely used, which is a reason to be careful when proposing to replace any part of it.

The PID rate loop has a known limitation. It uses no model of the vehicle and no measurement of how the vehicle is accelerating. A torque disturbance, such as a shifted centre of mass, a gust acting off the centre of gravity or a change of payload, is seen only after it has produced a rate error, and a constant torque offset is removed only as fast as the integrator accumulates it.

Incremental Nonlinear Dynamic Inversion (INDI) addresses this by using the measured angular acceleration. At each cycle it computes the change in torque needed to move the angular acceleration from its measured value to the desired one, and adds that change to the torque already being applied. A disturbance that changes the measured acceleration is compensated at the next cycle without being modelled. The model dependence of the controller is reduced to the control effectiveness of the actuators. The price is a dependence on sensors: the method needs a clean angular-acceleration estimate, filters that are synchronised with the signals they act on, and an accurate picture of what the actuators are already doing (chapters 2 and 3). INDI therefore trades model dependence for sensor and actuator-state dependence. Whether that trade is favourable on a PX4 vehicle is an empirical question.

## 1.2 Research question

The question addressed in this report is the following: can an INDI controller replace the PID angular-rate loop of a PX4 multicopter and do better, as judged by a benchmark whose scenarios, metrics and acceptance criteria were fixed in advance?

The words "fixed in advance" carry weight. The benchmark specification (`bench/scenarios.md`, version 1) was frozen before any INDI code existed. It defines the scenarios, the metrics, the paired-seed protocol and four acceptance criteria that lead to one of three outcomes: INDI outperforms PID, INDI matches PID, or INDI does not outperform PID. Scenarios are split into a tuning set, which both controllers may be tuned on, and a held-out set that was never used for tuning. The verdict is computed on the held-out set only, with the candidates frozen beforehand (decision D-freeze). The purpose of these rules is to prevent the common failure of controller comparisons, in which the new controller is tuned until it wins on the scenarios on which it is then reported.

## 1.3 Scope

The scope is deliberately narrow.

- Only the inner rate loop is replaced. The attitude and position loops are the standard PX4 controllers in both configurations.
- One airframe is used, the `gz_x500` quadrotor model of PX4 SITL.
- All evidence comes from simulation in Gazebo. No hardware flight was made.
- The comparison is against the PX4 PID rate controller. Other alternatives are not tested.

These limits mean that the results say how INDI and PID compare on one simulated vehicle, under one set of scenarios. They do not say how INDI would behave on hardware. The fidelity limits of the simulator, and what they imply for the conclusions, are treated in chapter 6.

## 1.4 Contributions

The work has four parts.

1. **An INDI rate controller inside PX4.** The controller is implemented as a library with unit tests and integrated in the multicopter rate-control module. It is selected at arming by the parameter `MC_RATE_CTL_TYPE`, and the PID path is the default and is left untouched (chapter 5).
2. **A reproducible benchmark.** A Docker image builds PX4 and runs Gazebo headless. A runner flies seeded, paired runs from a single command, and computes the metrics (chapters 6 and 8). The acceptance verdict was evaluated from those metrics against the frozen rules (`results/acceptance_s15.md`).
3. **Tuning of both controllers.** The PID baseline was searched for better gains and the search found none that beat the PX4 defaults, so the defaults are the retuned PID baseline. The INDI controller went through several tuning rounds, ending in a frozen candidate (chapter 7).
4. **Results.** The frozen candidates were flown on all six held-out scenarios with 10 paired seeds each, together with the tuning and disturbance scenarios, and the outcome is reported under the pre-declared rules (chapter 8).

## 1.5 Outcome in brief

Under the rules fixed before INDI flew, INDI does not outperform PID (`results/acceptance_s15.md`). This is stated here at the start because the rest of the report is easy to misread otherwise.

INDI has a clear advantage on disturbance rejection. Attitude RMS is lower than PID on every disturbance scenario, for example by a factor of 0.57 on the diagonal gust (H2) and 0.16 on the centre-of-mass shift (H3) (`results/heldout_s14.md`). Two weaknesses decide the verdict. First, under a mismatch between the actuator time constant assumed by the controller and the real one (scenario H5), INDI develops a 5-7 Hz roll limit cycle, and its roll-rate RMS on the rate-pulse part is 1.58 times that of PID (`results/acceptance_s15.md`). PID tolerates the same mismatch. Second, yaw is worse than PID whenever yaw is commanded. Criterion 3 therefore fails, and so does criterion 1, because both controllers crash on every seed of the double motor failure (H4). The verdict does not depend on H4, since criterion 3 fails on H5 alone.

Section 8.2 gives the full verdict, and chapter 9 discusses how far it generalises. The result is a trade rather than a finding that INDI is worse on average, but it is a loss under the criteria that were declared, and it is reported as one.

## 1.6 Structure of the report

Chapter 2 reviews the state of the art on INDI for multirotors, identification of control effectiveness, saturation, robustness and open-source implementations, and states the gaps addressed here. Chapter 3 gives the theory: rigid-body dynamics, the incremental form, angular-acceleration estimation, actuator dynamics and closed-loop behaviour. Chapter 4 analyses the PX4 multicopter control architecture and what it implies for an INDI controller. Chapter 5 describes the design and implementation of the controller. Chapter 6 describes the simulation environment, the scenarios and metrics, and the fidelity limits of the simulator. Chapter 7 documents the tuning of both controllers and the threats to validity. Chapter 8 presents the results, starting with the acceptance verdict. Chapter 9 interprets them, discusses the actuator-model sensitivity, yaw and the limits of the evidence. Chapter 10 concludes.
