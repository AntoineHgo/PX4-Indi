# G5.10 redefined, pre-test flights (S178, freeze-7 firmware = HEAD build)

Purpose: the two parts of G5.10 as amended by the owner (Q9 b/c), one INDI flight each (seed 1) plus the PID reference of
the same two flights, so the G5 verdict can be written. Evidence only; no gate numbers changed, no firmware touched.

## Definition used
- GATES.md row G5.10 (line 382): no LOC, altitude loss <= 2.0 m, tilt <= 20 deg, no windup (back within 0.3 m in <= 5 s
  after saturation ends). Owner amendments S175 (GATES.md lines 541-545, D-OWNER-Q8-Q15): (a) tilt limit = MPC_TILTMAX_AIR
  + 5 deg (read from the log, 45 + 5 = 50 deg); (b) the full-scale part is flown in STABILIZED, full throttle + full roll
  stick for 1 s, same limits; (c) the SAT part runs at a thrust scale where hover needs >= 1.0 command for 5 s, after a
  one-flight check that the motors sit at >= 0.99; the 73 % drop is a G3-type side probe, not a pass condition.
- SAT part: existing scenario `sat_sustained` (position mode, 3 m x step in "sat", 5 s) with an override
  (`sat_override.json`, existing `--scenario-overrides`): SIM_GZ_THR_SC 0.136 instead of 0.274. Hover thrust fraction is
  0.137 (D-THRUST), so hover needs 0.137 / 0.136 = 1.007 command: the motors are pinned at the top for the whole 5 s.
  Saturation is forced by the plant (available thrust), nothing else. The "agg" 37 m / 15 m up step of that scenario never
  saturated (S176 README) and is NOT used as the full-scale part; it is flown but ignored (g510_check reports it INVALID).
- Stabilized part: NEW scenario `g510_stab_full` (bench/scenarios.py) + 3-item `seg_sticks` spec (bench/stick_profile.py
  `seg_sample`, raw stick overrides). Why new: no existing scenario could command full throttle + full roll stick
  (`seg_sticks` had centred / pitch 3 m/s, `stick_steps` uses 0.5 of the stick). Segments: settle 3 s, full 1 s
  (y 1000, z 1000, i.e. full roll, full throttle), rec 9 s (centred). Flown with `--stick-mode stabilized`, no pilot.
- Plant flags as queue.sh of freeze7_s177: quad5in, sim v2, speed 4, matched GNSS 110 ms, vib-acc 10, vib-gyr 0,
  imu-noise-scale 4.0 (typical). INDI uses results/g5_freeze_s157/params.params; PID reference = `--controller pid`, stock
  params (as a56_pid_s173), same scenario / override / seed.

## Run
`nohup setsid bash indi_flight/results/g5_10_freeze7_s178/queue4.sh > .../queue4.log 2>&1 < /dev/null &` (repo root not
needed). It waits (<= 4 h) for QUEUE_END of freeze7_s177/queue.log and g2_outer_freeze7_s177/queue2.log, QUEUE3_END of
g2_spot_freeze7_s178/queue3.log, no queue*.sh process and no container named s177* / s178s*. Idempotent (a run dir with
flight.ulg is skipped), wall-clock `timeout 1000` per flight, status in queue4_status.tsv. Runs, in order:
indi_sat_s1, indi_stab_s1, pid_sat_s1, pid_stab_s1 (out dirs here; stdout logs `<name>.stdout.log`).

## Score (Docker, repo root; one line per run, replace <n>)
```
indi_project/docker/run.sh -n s178g510sc -t 600 -- bash -c '
 R=indi_flight/results/g5_10_freeze7_s178
 for n in indi_sat_s1 pid_sat_s1; do
   python3 indi_flight/bench/g510_check.py $R/$n --json $R/$n.g510.json > $R/$n.g510.txt
   python3 $R/score_motors.py sat $R/$n --json $R/$n.motors.json > $R/$n.motors.txt; done
 for n in indi_stab_s1 pid_stab_s1; do
   python3 $R/score_motors.py stab $R/$n --json $R/$n.motors.json > $R/$n.motors.txt; done'
```
- SAT: step 1 is the Q9 c one-flight check: `frac_any_ge_0.99` (and `frac_all4_ge_0.99`) over the 5 s "sat" window in
  `*.motors.txt`; the check holds if the motors sit at >= 0.99 for essentially the whole window. If it fails, lower the
  scale in sat_override.json and refly (the check, not the checker, is what Q9 c asks for). Then the g510_check lines
  no_loc / alt_loss / tilt / back_sat of the SAT part are the pass logic (the checker's 0.98 x 0.274 saturation test is
  trivially met at this scale, its AGG items are ignored; its overall RESULT will read INVALID/FAIL because of AGG).
- STAB: `*.motors.txt` gives motors >= 0.99 duration during "full", alt loss, max tilt vs MPC_TILTMAX_AIR + 5, LOC,
  `pass_limits`, and `level_5deg_after_sat_s` (recovery proxy, see doubts).
- g510_check.py and gate numbers are unchanged; score_motors.py is new and unreviewed.

## Open doubts
- With scale 0.136 the 5 s SAT part leaves almost no thrust margin; the 3 m step tilt and the sag may exceed 2.0 m altitude
  loss for any controller (the PID reference shows whether the test is physically passable). Owner wording "hover needs
  >= 1.0 command" is read as scale <= 0.137.
- Stabilized has no position setpoint, so "back within 0.3 m in 5 s" cannot be applied literally; reported as level
  (tilt <= 5 deg) time after the last motor >= 0.99 sample and altitude loss. Needs an owner/reviewer decision on the form.
- Nothing was flown yet (queue waits); the stabilized scenario path was not smoke-tested.
