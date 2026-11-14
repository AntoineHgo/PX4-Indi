# v2 held-out set (O-7): DRAFT, not frozen

Status: draft written in session 35 from OWNER_GUIDANCE step 6. It must be frozen (copied into `bench/scenarios.md`
as v2 with a change-log line and a commit) BEFORE the v2 INDI is tuned or flies any of these scenarios. Nothing
here has been flown by either controller. Sim config for every scenario: `--sim v2 --imu-rate 1000 --erpm-drop 0.01
--vib-acc 1.0 --vib-gyr 0.05`, `v2_fac.params` for both families (D-omega2: THR_MDL_FAC 0.683 for PID too).
Seeds 1-10, speed as in v1 (position scenarios at speed 1, D-speed). Metrics and acceptance criteria: the v1 rules
of `results/acceptance_s15.md`, unchanged, so v1 and v2 outcomes are comparable.

## New held-out scenarios (never used for tuning)

| id | aims at | definition (draft) | sim support |
|---|---|---|---|
| V1 | v1 weakness: slow actuator | step pattern + rate pulses (as H5 att/rate) with plant motor tau x2 (up and down) | `model_variant` tau (exists) |
| V2 | asymmetric actuator | same pattern, tau up x1, tau down x3 | NEW: separate up/down factors in `model_variant` |
| V3 | ESC telemetry latency | same pattern, eRPM latency +2 ms over the AM32 model | NEW: gz_bridge has no latency param (SIM_GZ_ESC_FB 2 adds one output period only) |
| V4 | eRPM dropouts | same pattern, 20 % frame drops, plus a 2 s total eRPM loss on one motor mid-window | drops exist; NEW: timed total loss |
| V5 | vibration | hover + step pattern with vibration x3 (vib-acc 3.0, vib-gyr 0.15) | exists |
| V6 | battery sag | step pattern while available thrust falls 15 % over the window (motor max speed ramp) | NEW (sim side, identical for both) |
| V7 | strength: gust | gust_diag profile (H2) on v2 config | exists |
| V8 | strength: CoM shift | com_shift profile (H3) on v2 config | exists |
| V9 | strength: motor loss | T8 motor_loss_0 at onset in hover, v2 config | exists |

"Seen" set, reported separately and labelled as such: H1-H6 and T1-T8 re-flown on the v2 config.

## Open choices to settle at freeze time (record in DECISIONS.md)

- V2 factors: x3 on the down constant only is a guess at an ESC without active braking; check against the AM32
  note (`research/notes/`) before freezing. Checked s35: `research/notes/am32_erpm.md` says nothing on braking
  (no hit for brake/braking); keep the guess flagged, or source it elsewhere.
- V3: what latency the real AM32 + BDShot chain has beyond the model (the model already includes one telemetry
  period); +2 ms is a placeholder. Checked s35: the AM32 note finds no fixed turnaround constant (telemetry sent
  from the DMA-complete path, sub-ms); the larger latency is the speed estimate from commutation intervals and the
  PX4 DShot driver's esc_status rate, neither quantified yet.
- V6: implement as a time ramp of the motor max rotor speed in the sim (both controllers see the same plant); PX4
  battery compensation stays at its default for both.
- Whether V1/V2 use the full H5 combination (inertia and mass mismatch too) or actuator only. Draft: actuator only,
  so the cause of any loss is attributable; H5 itself stays in the seen set.
