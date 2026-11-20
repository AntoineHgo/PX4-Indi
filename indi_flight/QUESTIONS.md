# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

Q7 closed S140 (owner answer A: G5.7 validity at the 4 edges leaving posctl; written into GATES 5b; text in JOURNAL.md).

## Q8 (S143, 2026-11-20): G5 event injectors, G1.5 timing and two rows not injectable firmware-free. NOT blocking.
Context: S142 built bench/g5_events.py (one flight: EKF yaw/xy reset, RC/link/offboard loss, kill/re-arm), pre-test
in results/g5_events_s142/README.md. (a) Every MAVLink-side event is applied 3-24 ms after its commanded time: the
runner only acts on lockstep ticks of 10-20 ms. G1.5 asks "applied within 1 physics step (1.25 ms) of commanded and
logged as applied". The applied time IS logged by the firmware itself (kill flag, failsafe flags, EKF reset counters).
(b) G5.6 false maybe_landed and G5.11 EKF z reset cannot be produced without firmware: the land detector needs
ground contact, and the external-position reset in ekf2 is horizontal only.
Options (a): A [recommended] for discrete events (stream stop, kill, EKF reset command) the G1.5 timing check becomes
"applied time taken from the firmware's own log flag/counter, every G5 transient metric referenced to it, the
commanded-applied spread reported"; the 1-step rule stays for physics injectors (torque, wind, motor, eRPM). This
fixes a defect of the test (the rule exists so metrics start at the real event), it does not loosen a G5 limit.
B: build a sim-time event scheduler (gz plugin or firmware hook), about 2 sessions.
Options (b): A [recommended] SITL-only test parameter in the two INDI modules (not in stock modules, O-11 holds) that
forces maybe_landed into their own land input for 0.5 s; z reset: try an EKF2_HGT_REF switch in flight (param, no
firmware), else row "not tested" with this reason. B: mark G5.6 false maybe_landed and G5.11 z as not tested.
Meanwhile: fix the ekf_yaw and rc_loss injector defects and continue G5.5 (A18); event rows fly after G5.7/A18.
Q8 addendum (S144): yaw-reset and RC-loss injector defects fixed and keyed (results/g5_events_s144). With applied time
taken from the firmware log, command events are 1.75-4.25 ms after send (ekf_yaw 3.0 ms). For stream-stop events
(rc/link/offboard loss) the firmware has no "applied" instant other than the failsafe flag, which includes the
timeout; the G1.5 1-step check cannot apply there and those G1.5 FAIL lines are by construction, not evidence. The
G5.8 limit (failsafe <= 1 s after timeout) is checked as written. Option (a) A covers this; still not blocking.
Q8 addendum 2 (S146): G5.9 "motors 0 within one command period" referenced to manual_control_switches.kill_switch
measures 5.00 ms (FAIL vs 1.25 ms, fix_s2), all of it stock commander latency switch -> actuator_armed.kill; outputs
are 0 in the same sample as the kill flag (0.00 ms). Options: A [recommended] reference = actuator_armed.kill rise
(the instant the control stack is told; commander latency reported, O-11 forbids changing it); B keep the switch
reference: G5.9a FAIL recorded as a stock limit. Meanwhile: both numbers reported, row counted FAIL. Not blocking.
Q8 addendum 3 (S146): G5.8 definitions, two items, not blocking (results/g5_events_s146_move/README.md).
(i) "excursion <= 1 m" at 3 m/s: measured from the position at loss it includes the flight during the timeout
(4 s offboard timeout = 12 m) and the braking (3.4-3.5 m from 3 m/s, stock hold). Options: A [recommended] excursion
at 3 m/s = max horizontal deviation of ground truth from the position setpoint/trajectory the failsafe action
commands (what the controller controls), <= 1 m; hover keeps the current definition. B: drop the 3 m/s excursion.
(ii) link_loss "timeout": the firmware flags GCS loss COM_DL_LOSS_T after the last telemetry_status heartbeat flag,
which itself stays set about 2.25 s after the last GCS message (fix_s2: last message 75.35 s, entry 80.60 s; stock
mavlink/commander, O-11). Options: A [recommended] timeout reference = firmware's own flag (as now, S144 note), the
receiver window reported; B: reference = last message sent, row FAIL in both stacks (stock limit).
Meanwhile: G5.8 hover counted on the S144 definition with the 2.25 s window reported; 3 m/s rows not counted.
