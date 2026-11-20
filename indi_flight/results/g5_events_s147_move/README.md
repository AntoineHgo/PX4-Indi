# G5.8 3 m/s re-fly, s1 (S147) — probe, not counted

Why: key2 S146 BLOCKING B1 (--moving recorded hover t_cmd_us; checker searched from the wrong instant). Fixed in
6b623d589e (t_cmd = schedule time of the dispatched event; f_ob_stop drops the velocity setpoint, M1) and the
follow-up commit (t_cmd cleared after dispatch: unkill/rearm/takeoff2 keep sim.t; this flight's run.json corrected
for those three, marked `t_cmd_note`, their t_cmd = t_applied as intended).
Command: S146 README line 13 with `--out indi_flight/results/g5_events_s147_move/s1`.

Event times now consistent: t_cmd vs applied 0-3 ms for every scheduled event (rc_loss 55.187/55.190 s, ...).
g5_rows_check.py (unchanged):
- rc_loss entry-timeout 510 ms, link_loss 1 ms, offboard_loss 21 ms (<= 1000): PASS on the S144 reference; all enter hold (nav 4).
- excursion 5.39 / 12.47 / 15.56 m: FAIL by definition at 3 m/s (timeout flight + braking), Q8 addendum 3 (i) open.
- G5.9a kill: actuator_armed.kill 3.75 ms after the switch, outputs 0 at the flag (as hover, Q8 add. 2); 9b/9c/9d PASS.
Key2 M1 (a) remains by design: after rc/link resume the 3 m/s stream continues until the next leg; the vehicle is in
hold then, the setpoint is not followed. M2: speed at loss verified 2.99-3.00 m/s in S146 (same schedule).
Next: 3 seeds once Q8 addendum 3 (i) is answered.
