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
