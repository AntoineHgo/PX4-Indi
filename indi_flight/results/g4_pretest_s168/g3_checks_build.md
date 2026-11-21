# g3_checks build notes (S169)
Files: bench/g3_checks.py, bench/tests/test_g3_checks.py. Run in Docker (g3chk). Not committed.
## Spec readings
- Truth = sim_ground_truth (x,y,z NED, q, angular_velocity), stamps timestamp_sample (as g4_metrics), grid = g4_metrics.uniform.
- Item 1 LOC, item 2 detector (rates 2-40 Hz, 4 s/1 s, >20 x median, RMS>5 deg/s at peak, >=3 windows +-10 %), position limit
  cycle (3 x 10 s, p2p>0.3 m detrended), G4 chatter (actuator_motors 20-100 Hz, >20 x median, per motor), item 3 as in GATES.
## PROPOSED (listed in module docstring)
- airborne span = first height>1 m .. last >1 m or first nav_state RTL(5)/AUTO_LAND(18) (commanded descent not scored).
- height drop reference = height at T0; ground contact = height<0.1 m in span; horizontal excursion only in position mode.
- reference = median trajectory_setpoint position in [T0,T1] (fallback truth window mean, reported).
- mode position gates horiz RMS + alt mean; attitude gates roll/pitch mean only.
- position limit-cycle windows from T0 to end of span; run freq tolerance vs first window of run.
- controller fault flag NOT implemented (undefined); NaN check only.
## Self-test (7 cases) PASS: clean, osc30 8 dps RMS (fails item2), osc30 4 dps (passes), 60 Hz command line (chatter),
   position limit cycle, landing (excluded), 0.2 m altitude offset (item3), tilt 80 deg (item1).
## Break-check (--break-check, thresholds patched, matching case must change): all caught
   RMS_DEG_S->1e9 (osc30), CMD_BAND->100-150 (chatter60), POS_P2P_M->9 (poslc), ALT_MEAN->9 (alt_off), TILT_DEG->179 (loc).
   Not break-checked: nan, ground contact, height drop, excursion, landing exclusion.
## Smoke hoverL_harsh_s1, window 37-92 (json: hoverL_harsh_s1/g3_checks.json), overall pass False
- airborne 11.5-96.0 s. Item1 pass (tilt max 1.1 deg, drop 0.04 m, excursion 0.11 m). Item3 pass (horiz RMS 0.045 m, alt mean 0.055 m).
- Item2: p,q,r and position not sustained. Command chatter SUSTAINED on all 4 motors: line ~70 Hz (69.75, 70.0 Hz) from
  ~t_air+6 s for 72-75 windows, plus a 22-24 Hz line in 3 windows at ~t_air+3 s (takeoff). Cause not investigated.
