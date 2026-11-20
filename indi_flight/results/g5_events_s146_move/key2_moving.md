# Key2 review: g5_events.py --moving (commit 71f4be9ece)

## BLOCKING
- B1. Event t_cmd_us is wrong in --moving. ev() calls in f_rc_off/f_rc_on/f_hb_off/f_hb_on/f_ob_pre/f_ob_mode/f_ob_stop/f_ob_hold/f_kill
  (g5_events.py:108,112,116,121,126,130,134,138,142) still use T0+TIMES[...] (hover schedule); the moving schedule (lines 145-163) does not
  change them. s1/run.json confirms: rc_loss t_cmd 63.126 s vs applied 54.128 s; link_loss 75.126 vs 72.128; offboard_loss 97.126 vs
  90.128; offboard_mode t_cmd 93.126 on all three (applied 47/65/83); kill 112.126 vs 102.128. The checker (lines 231, 295, 302-306, 313)
  uses t_cmd_us for the failsafe-flag search window (first_rise from t_cmd-100 ms, and `t >= t_cmd`), and for dt_app. Result: the search
  starts 9 s (rc), 3 s (link), 7 s (offboard) after the real event, or the verdict is wrong or missing. Not the "same format" requirement.
  Fix: pass the commanded time to the event (e.g. event functions take a t_rel argument or read a st["t_rel"] set by at()), or have at()
  wrap fn to record its t_rel. Also offboard_stream_on in moving mode has the right t_cmd (line 150), so only the loss/resume/mode/hold/kill ones break.

## MAJOR
- M1. Stale velocity setpoint: st["vel"] is never cleared (lines 56-57 gate only on "vel" in st). After f_ob_stop sets ob=False the stream
  stops, so no stale send occurs today. But (a) after rc_resume/link_resume the 3 m/s stream keeps running until the next leg (~5.5 s and
  ~7 s of old setpoint while the failsafe has changed the mode to hold; if the mode ever returned to offboard the vehicle would fly the old
  velocity), and (b) f_ob_hold / hover-style f_ob_pre would re-use "vel" priority over hold_ned if st["ob"] becomes True again (not used in
  moving, but latent). Recommend: f_rc_on/f_hb_on (or the failsafe events) set st["ob"]=False and pop "vel", or pop "vel" in f_ob_stop.
  Also leg 1/2 'on' replaces vel and hold_yaw atomically, which is fine.
- M2. Steady 3 m/s is not asserted: leg 0 loss is 9 s after stream start (7 s after offboard mode); leg 1 starts from a vehicle that was
  put into hold by the rc failsafe, at 3 m/s reversal -3 m/s (about 6 s to flip after mode at +2 s). Likely fine in SITL but not checked in
  the script; vz=0 velocity-only setpoint gives no altitude hold guarantee beyond the controller. Verify from the log (speed at loss).

## MINOR
- m1. mv_leg `name` parameter unused (line 144-ish). Legs' loss functions run in offboard only if the mode switch succeeded; no check.
- m2. Without --moving: behaviour identical. Same ev/at calls in same order; the extra `if "vel" in st` in tick is false because "vel" is only
  set in moving; --moving is stripped from sys.argv before argparse. Re-indent only. OK (spec 1 satisfied).
- m3. Moving timing is deterministic in sim time (at() on T0+rel, sim.t driven), spec 2 timing OK apart from B1 labels.
- m4. Moving flight omits ekf_yaw/ekf_xy events; the checker should tolerate absent events (not verified here).
