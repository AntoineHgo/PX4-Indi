# G3 probe S117 (RC113: probe of the current stack, NOT gate evidence)
Campaign `g3_sample.campaign(117, 60)` after D-G3-STICK-FACTORS (981e94f79e): 45 position (o1_lemniscate --sched),
10 stabilized, 5 acro (stick_zsine_o6), 12 corners. Base params bench/params/quad5in_indi_g1.params, INDI, 800 Hz.
Command: `bash indi_flight/results/g3_probe_s117/fly.sh 3 <idx...>` (one container per run, progress.txt).
Per run: run_NNN/g3_done.json (outcome), g3_draw.json (draw + command), metrics.json, run.json. Raw ulg untracked.
Set-up note: the first launch of idx 2-59 passed the list as one zsh word, so only idx 2 flew; 3-59 relaunched.

## Pre-test (idx 0 acro, 1 position, 16 stabilized)
- 1 and 16: ok. 0 (acro; mass 0.76, tau x2.35, asym 2.76, delay 10 ms, G1 e 1.46/0.73/0.55): watchdog
  "> 3 m below hold altitude" at sim 59.8 s.
- Cause (log): stick segment from ~51 s holds collective 0.1 = HTE absolute lower bound (zero_order_hover_thrust_ekf
  clamp 0.1, true hover at mass 0.76 is about 0.10), acro holds the tilt it reaches (11.4 deg, no levelling), so the
  vehicle sinks 3.5 m in 6 s.
- PID control on the same draw (ctl_pid_run000.sh): sinks 2 m in the same window (z -5.0 -> -2.95 at 56 s), holds 32
  deg tilt, then the zsine throttle pushes it to 159 m; no watchdog trip, run ends on a wall timeout in landing.
- Verdict: acro stick_zsine_o6 leaves attitude AND altitude open-loop; outcome is chaotic for both controllers and
  says nothing about the controller (O-13). Acro rows of this probe are scored "scenario-invalid" until the stick
  runner has a pilot model (D-G3-STICK-PILOT, proposed S117).
