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

## Batch result (60/60 flown, summary.txt from summary.py)
- position 45/45 ok (incl. corners C2 sag+heavy+low G1, C3 saturation+gust, C4 GNSS mismatch+wind 5 m/s, C6 weak motor).
- stabilized 8/10 ok; acro 3/5 ok. Non-ok: 0 (acro), 21 (stab), 25 (acro), 49 (stab, corner C1).
- "ok" = no watchdog/abort only. No oscillation detector, steady-state or tracking limit is scored yet
  (g3_checks.py does not exist): this is NOT a G3 pass of any item.
- PID controls (ctl_pid.sh <idx>): run 21 PID also hits the ground (height < 0.3 m at 71.2 s vs INDI 67.2 s).
  Run 49 (G1 e = 2 all axes, tau x3, asym 1.2, delay 10 ms, vib x3.1): PID flies it, INDI sinks 3.4 m; both command
  the same mean collective (0.133 +- 0.001 over 62-77 s) and show the same roll-rate RMS (84 dps at 77 s, the stick
  profile), altitude drifts +-3 m open-loop (INDI down, PID up). A 0.3 % thrust difference crosses the 3 m line:
  not discriminating. Same cause as run 0: open-loop collective (D-G3-STICK-PILOT). Run 25 (acro) not controlled.

**S121 VOID for INDI:** the "indi" runs here flew the stock rate loop (MC_INDI_EN=0, no boot_params in run.json; base params lacked MC_RATE_CTL_TYPE 1). See JOURNAL S121.
