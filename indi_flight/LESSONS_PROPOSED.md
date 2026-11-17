# Lessons proposed (not read at launch)

Rules learned in stage 2, proposed for LESSONS.md (the owner promotes them). Append new ones at the top of the
list, one rule with the event that produced it. Read the cost entries before sizing an agent brief.
Moved out of STATE.md on 2026-11-17 (token economy, owner).

- S64: a gate-text draft quoted hover command 0.137 as implying T/W 53; on this airframe T/W is 7.3, so the owner's
  "available thrust 0.7" saturates nothing. Size every saturation/sag test on hover thrust of the flown model, not on full scale.
- S63: re-run the metric with the fix before writing what an artefact was: the seed3 roll 'exit' was attributed to
  the return step in a committed README and the fixed-window re-run disproved it the same session.
- S62: a model calibrated on one flight (S61) predicted the fix to 1 point of overshoot on 3 seeds; the setpoint-path
  change cost one sonnet task (~$0.5) and 12 flights. Fit the closed loop on flight data before choosing a law change.
- S61: a 'lead' that is feedback-only lowers the closed-loop bandwidth seen by the outer loop; margins at the inner break
  looked good (PM 59-87) while the attitude step overshot 13 %. Check the outer loop's step response with every inner-loop
  law change, not only the inner break margins.
- S60: a 'published = stock mapping' residual check is blind when the two chains agree at steady state (hover, no gap);
  prove which law flew with an in-module instrument (state bits in the log), and test the law where it differs (thrust gap).
- S58: the px4_sitl_test build does not compile the module (only libs and tests); a coding agent's green tests say nothing
  about the module wiring: always add `make px4_sitl_default` to the brief.
- S57: a non-integer fs*Tp did not trip the FFT check on a jittered log because the FRF code switched to its least-squares
  path; know which path a script took before calling a pass a hole. Pick multisine periods that are whole samples at every rate.
- S54: a module-level loop variable shadowed a deleted local in a model script and silently changed its output; re-run
  every model script against its committed output after any edit (diff), as done here.
- S53: four M3a flights on two parallel docker streams took ~5 min wall and ~$0.05 of context: run small sweeps
  from host bash in the background while one agent drafts, instead of delegating the flights.
- S52: review F2 named the over-estimated ACT_TC as the dangerous side of the lead; test and flight show the opposite
  (x0.6: PM 42, x1.4: PM 83). Compute both sides of a parameter error before planning defaults around one.
- S51: an opus review of a ~180-line note plus ~400 lines of law code cost ~$1.1 in 9 calls (2x the S35 estimate); budget opus reviews at ~$1.1 and launch them first in a session.
- S50: break-checks by sed on a .py must run with PYTHONDONTWRITEBYTECODE=1 (or clear __pycache__): a same-size
  mutation in the same second left a stale .pyc that made the restored file fail.
- S49: calibrate the unmodelled delay of a loop model on one existing flight before using the model to accept or
  reject a candidate; the lead's verdict at 400 Hz flips between 2.5 and 5 ms of delay.
- S48: before reading a low margin as a plant or gain problem, put every loop the break closes around into the model
  and test it by predicting a parameter change in flight (two flights, ~$0.1 of CPU, settled what 7 sessions had not).
- S47: a single clean flight does not prove stability: S45 hovered clean, the same config limit-cycled on replay (bistable
  lightly damped mode). Accept a configuration change on >= 2 seeds, and derive every term of the law (G2 too) before flying.
- S43: a static 'analytic' gain from source reading was 2.6x off in two links; measure each link of a chain on the log before trusting a derived plant gain (and a sonnet chain trace with log analysis costs ~$0.9 in 17 calls).
- Regressing a filtered signal (angular_accel_filtered) on a command: pass the command through the same filter first; T86 missed it and read the LPF2p group delay as a 20 ms plant delay (S42).
- S41: a loop-gain model must contain every loop the break closes around, outer loops included; the M3a model
  lacked the attitude P loop and a 17 deg PM gap was spent on as an anomaly (A-21).
- S39: a sonnet implement+build+fly task asked to add a unit test spent its last calls on a link error; tell it the
  gtest kind (unit = pure code) and the test build dir, or leave the test run to a separate step.
- S37: a sonnet task writing ~600 lines of numerical code + tests costs ~$0.9 in 9 calls (long writes); the session
  takes one such task plus a haiku second key.
- S36: a design note on a loop with several feedback paths must name every path a break point cuts; the gyro break
  looked complete for PID and was not for INDI (review r1).
- S35: a sonnet design note of ~11 calls over several source files costs ~$0.7; brief it at <=10 calls at a $3 cap.
- S34: a background-wait notification can arrive before the command really ends; check the condition itself
  (status file) before concluding the wait failed.
- An anomaly bound taken from the range of 10 runs was exceeded by the next 5 (A-19, S32): bound by mechanism.
- A metric changed during a running batch: re-compute the whole set with one version before comparing (S32).
- A shared sim model is live for every running batch: stage a model change and install it after the batch ends (S28 nearly mixed two baro models into B26).
- A parked anomaly bound from a correlation (A-14: 0/9 vs 3/6 runs, p=0.044, "logger -f") was wrong; park on a mechanism, not on a pair test (S27).
- A sonnet implement+build+2-flight task costs ~$1.0 (21 calls): at a $3 cap it is the session's one big task (S26).
- Read the sleep/wake rule of a loop before building a timing fix around it: S25 spent a session on a start-up
  race while Commander's skip-sleep-on-command line (visible in 20 lines of source) already ruled it out.
- A pre-test check worded "within N periods of the command" measured Commander's fixed latency; state the
  determinism check as across-run spread, and latency separately (S24).
- Give each anomaly at most 2 sessions, then park it with a written bound and reopen trigger (route check 22).
- Haiku handles a well-specified log check (10 calls) for ~$0.06: use it for every bounded log/metric check.
- At a $1.6 cap: one sonnet agent of ~15 calls (~$0.5) plus state and commit; no fable work.
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- A fable review of ~1 KLOC of design + source costs ~$2.5: give it a whole session.
- Opus with a narrow brief (one interface, <=12 calls, early skeleton write) reviews ~200 lines of design + source
  for ~$0.6: use opus, not fable, for design review rounds.
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
- PX4 logger default timer (3.5 ms) silently decimates topics above 285 Hz; poll on the last topic of the control
  cycle (`-p actuator_motors`) and check logged rates (`bench/check_rates.py`) before any high-rate analysis (S16).
- At a ~$1 cap the launch context alone costs ~$0.3: do one host-bash flight + check, no agent (S19).
- Analysis scripts take an output path argument; never a fixed path into a committed result (S19).
- Anchor every analysis window on an event in the log, never on the runner's view of it: the 1 Hz HEARTBEAT view moved the window start by up to 0.95 s (S15).
- Give a second key the primary script's exact window (start, end, anchor); a different window produced a false 2.1 % DISAGREE (S23 T48).
