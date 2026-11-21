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

## Retry S184-F (no PID flight; scenarios.py restored, patch kept as sat_ramp_F_attempt.patch; fly_f.sh = fly.sh with outputs *_satF_s*)
- T/W at scale 1: 7.31 (gz motorConstant 1.5e-6, max rotor speed 2700 rad/s -> 4 x 1.5e-6 x 2700^2 = 43.7 N; mass 0.610 kg incl. rotors, design/gates_g3_g8_final_s94.md:5, design/ref_airframe_data.md:59,86).
  Log cross-check (indi_satF_s1 esc rpm at hover): omega 999 rad/s -> (999/2700)^2 = 0.137 hover fraction, T/W 7.3. thrust_scale is cumulative (fault_apply multiplies, `reset` returns to 1), applied to SIM_GZ_EC_MAX x sqrt(scale).
- Final scale chosen s = 1.08 / 7.31 = 0.1477 (hover cmd 0.928, 1.08 x weight at full cmd). Flown INDI s1 twice (2 of 4 flights):
  1. 17 x 1 s steps of +0.05 hover cmd (to 0.928): sank from cmd ~0.7 (scale ~0.19), z 4.9 -> 0.26 m, watchdog at 74.6 s, no 'sat' event.
  2. 8 x +0.05 steps to cmd 0.5, then 20 geometric steps of +3.1 %/s to 0.928, plus 3 s hold: still sank from cmd ~0.65 (z 4.94 -> 1.6 m, vz 0.4-0.5 m/s), watchdog (3 m below hold) at 84.8 s, no 'sat' event.
- Cause (flight log, not a plant limit): rotor speed stays at 1000-1004 rad/s = hover all through the ramp (T/W 1.00-1.02, not above), and the controller never raises thrust above the need.
  `hover_thrust_estimate` stops at 0.337 from t=65 s on (MPC_THR_HOVER 0.137, MPC_Z_VEL_P_ACC 4, I_ACC 2, MPC_THR_MAX 1), while the true hover cmd rises to 0.65-0.93.
  PX4 scales the vertical accel -> thrust gain by the hover estimate, so at hover cmd 0.7 the vertical loop has ~2x too little gain per m/s of sink (and I-term 2x too slow) and cannot recover the sag: a sink of 0.4 m/s persists with thrust = weight.
  That is why both stacks (PID too) sank at scale < ~0.2 in all ramps; it is independent of the ramp rate and of T/W (margin 1.08 was real: omega max 1038 vs hover 999).
- Verdict: set-up NOT valid; scale-down of SIM_GZ_EC_MAX cannot give a pinned-at-top hover with stock PX4 hover-estimate bounds. No score meaningful (scorer: FAIL, no 'sat' event). PID not flown (same law).
- Options for the owner (all outside this pre-test): (a) raise MPC_THR_HOVER / the HTE upper bound in the flight params for this scenario (changes the stock hover, owner decision); (b) reach saturation by a demand transient at a larger scale (e.g. 0.3-0.4, hover cmd 0.34-0.46, the hover estimate bound covers it) instead of by pinning the hover; (c) reduce hover thrust margin by adding mass (model payload) rather than reducing max omega, the PX4 hover cmd stays 0.137 only if thrust per cmd is unchanged, so this also needs (a).
