# RECONCILE_S227: G3 scorer wiring fixes and key 1 / key 2 reconciliation (S227)
No flights, no builds. Interpretations of both keys unchanged.

## (a1) Wiring fixes
- bench/g3_chain.sh:524 (key 2 args taken from key 1's printed line; g3_score.sh prints `--run-json` for S214 runs, `--t0` for old runs)
  before: `args=$(grep -E "^$r --t0 " "$d/chain_key1.txt" | head -1 | cut -d' ' -f2-)`
  after:  `args=$(grep -E "^$r (--t0|--run-json) " "$d/chain_key1.txt" | head -1 | cut -d' ' -f2-)`
  (`bash -n` ok). Without it args was empty for every G3-scenario run and key 2 was skipped.
- bench/g3_checks_key2.py:412 (the "line 225" is the window code; position_mode is set at 412):
  before `position_mode=rj.get("scenario") == "o1_lemniscate" or rw["mode"] == "position"`
  after  `position_mode=rj.get("scenario") in ("o1_lemniscate", "g3_lemniscate") or rw["mode"] == "position"`
  Already worked via the `traj` event (rw["mode"] == "position"); the edit makes it explicit. g3_stick_zsine NOT added: it is a
  stick scenario (attitude/rate mode, `stick` event), position gates do not apply (GATES item 3 roll/pitch in attitude mode;
  KEY1 POSITION_SCENARIOS also excludes it; g3_score.sh pos = o1_lemniscate/g3_lemniscate only).
- Tests (/tmp/g3venv, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1): key 2 `g3_checks_key2.py --self-test` 17 PASS 0 FAIL, rc 0;
  key 1 tests/test_g3_checks_s226.py 10 passed; tests/test_g3_checks_key2_s226.py + _q14_q15.py + test_g3_run.py 38 passed.
  (key 1 has no --self-test; tests/test_g3_checks.py collects 0 tests.)

## (a2) Items 5 and 6
GATES item 5 (line 312): "after each injected event (gust, fault start) back within 0.3 m and 3 deg of the pre-event reference
in <= 5 s and no re-excursion > 0.3 m for 5 s". Item 6 (line 314): "body rate RMS <= 5 deg/s over the last 20 s with zero sticks".

| Point | Key 1 | Key 2 | GATES supports | Recommendation |
|---|---|---|---|---|
| 5 reference | commanded path at the same time: trajectory_setpoint + q_d (g3_checks.py:273-285 docstring, :297-302) | position mode: trajectory_setpoint + q_d, same (g3_checks_key2.py:267-297); attitude mode: median body z over 2 s before event (:299-301) | "pre-event reference": ambiguous. Literal reading = state before the event; the S214 text moves events to the start of the main trajectory, where a static pre-event point does not exist, so the commanded path is the only definable reference in position mode | Keep both (they agree in position mode). Owner to confirm "commanded path" in one GATES line. Stick runs: key 1 uses tilt vs q_d, key 2 pre-event median; differ, ask owner |
| 5 smoke 0.67 m | quiet-window max 0.67 m on run_001 (KEY1_README:43-45) is tracking error: item 4 allows 0.5 m horizontal RMS, band is 0.3 m 3-D, so item 5 is stricter than item 4 against the same reference | same reference, same band, so the same effect expected (not measured here, UNVERIFIED) | text ambiguous: band 0.3 m is given, but "re-excursion" suggests deviation caused by the event | Owner decision: either keep (item 5 then binds on tracking; 0.3 m < item 4 RMS limit) or score re-excursion relative to the pre-event tracking error. Do not change silently |
| 6 axes | per-axis p, q, r each <= 5; vector RMS reported only (g3_checks.py:323-333) | one 3-axis vector RMS sqrt(mean(p2+q2+r2)) <= 5; per-axis reported (g3_checks_key2.py:322-332) | ambiguous ("body rate RMS"). Vector RMS <= 5 implies each axis <= 5, so key 2 is the looser test by up to sqrt(3) per axis | Adopt per-axis (key 1: stricter, matches p,q,r wording of item 2); owner to confirm; both numbers are already reported |
| 5 gated on telemetry events | no: events = fault/gust step start only (KEY1_README interp. 1) | no: gated = main-segment start; telemetry loss/frozen are reported-only, gated=False (:279, `extra`) | "injected event (gust, fault start)": telemetry loss is not named, so both consistent with text | Keep. Both report/skip telemetry the same way for gating |

Other difference noted (not in the asked list): key 2 fails closed if the flight ends < 10 s after the event; key 1 requires the log to cover the 5 s quiet window (log_covers_quiet_window).

## (a3) Hold length
- Scenarios: bench/scenarios.py `G3_HOLD_S`, used by g3_lemniscate and g3_stick_zsine (one constant). Was 25.0.
- Requirements: S214 hold >= 20 s (item 6 needs the last 20 s; item 3 the last 10 s). Position limit cycle (GATES item 2,
  3 consecutive 10 s windows): key 2 `pos_limit_cycle(hold0, hold1)` (g3_checks_key2.py:79, called :346) takes windows from the hold start,
  so 25 s gives windows at 0 and 10 s only (2): can never flag. It needs hold >= 30 s exactly; 35 s leaves 5 s margin for the
  actual arrival time and sample coverage (the log must also cover the hold end).
- Change: G3_HOLD_S 25.0 -> 35.0. File changed: bench/scenarios.py. Tests re-run after the change (counts above): pass.
  Adds 10 s per G3 flight (about 50 min over 300 runs); wind hold_to_end and the sag final value follow the scenario end automatically.
- FINDING (not changed, key 1 interpretation): key 1 `position_limit_cycle` is called with start `max(ta, t0)` (g3_checks.py:387) and
  t0 = item-3 window start = last 10 s of the hold under --run-json, so key 1 evaluates one window and can never flag a limit cycle.
  Key 1 would need its start at the hold start (or the main-segment start) for 3 windows. Owner/orchestrator decision.
- UNVERIFIED: no real G3-scenario log exists; run-time limits (g3_run/g3_chain timeouts, docker -t 900/500 for scoring) not re-checked
  for the 10 s longer flight; test_g3_run.py only asserts G3_HOLD_S >= 20.
