# G5.10 SAT set-up fix pre-test (S184), seed 1, INDI and PID, freeze-9 config, no firmware edit, no commit

Change: bench/scenarios.py `sat_sustained`: 18 ramp segments (1 s each) between "settle" and "sat" with cumulative motor_fault
factors, so SIM_GZ_THR_SC goes 1 -> 0.136 during hover (hover command 0.15 .. 0.95 in 0.05 steps, last 1.007) and "sat" starts
already at the limit. Why: the old scenario stepped the scale 1 -> 0.136 together with the 3 m step (D-G510-SAT-SETUP, an 86 % thrust-loss test).
Scorer and thresholds unchanged. The ramp uses the existing per-segment motor_fault, applied at logged event times (run.json events/motor_fault.entries).

Command per run: `indi_flight/results/g510_setup_s184/fly.sh <indi|pid> <seed>` (docker run.sh, timeout 1000, nominal plant flags
--gps-dly 110 --gnss-delay 110, INDI with g5_freeze_s157 params, PID without; then g510_score_motors.py -> <out>.score.txt).
Attempts (INDI s1): 4-step ramp (1 s steps): fell at T/W~1 during ramp, crash in sat; 6-step: fell before sat; 9 steps of +0.1 cmd: fell
(thrust loop lags 0.1/s); 18 steps of +0.05 cmd: INDI followed the need up to cmd ~0.7, then sank (z 4.9 -> 0.06 m) before "sat" started, 
run aborted (no 'sat' event, scorer FAIL/loc, not a valid test). Final PID s1 run (same scenario): command followed to ~0.8, then sank; watchdog at sim 78.88,
scorer INVALID (all-4 saturated 0.75 s of 5, alt loss 2.39 m, window covered 2.5 s).

Result: set-up still NOT valid. Both stacks sink once the commanded hover thrust passes ~0.75-0.8, long before 1.0, so the plant gives less
thrust per command near the top than the linear hover model (0.137/scale) says (or rotor/battery limit): T/W at scale 0.136 is below 1 in practice.
This is the D-G510-SAT-SETUP overturn case (PID also fails) -> owner question: scale 0.136 is unreachable by any controller; need a larger scale
(e.g. 0.16-0.18, a hover command ~0.8-0.85) or a measured hover command at the limit. Not verified: the true max-thrust to command map (check rotor rpm vs
cmd in indi_sat_s1/pid_sat_s1 flight.ulg at 70-76 s); INDI 18-step score text is the stub above (no window).
Seeds 2-3 NOT to be flown with this setup. After the scale is decided: `for s in 1 2 3; do for c in indi pid; do indi_flight/results/g510_setup_s184/fly.sh $c $s; done; done`.

S184 orchestrator: the scenarios.py ramp change is reverted (invalid set-up, both stacks sank); kept as sat_ramp_attempt.patch. Next: set the final scale from the model max thrust / weight (target ~1.1 x weight at full command), not from the linear command model.
