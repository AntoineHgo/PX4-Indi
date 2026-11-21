# G4 gate batch (S169) -- 18 runs, serial, 3 seeds

Config: freeze firmware 23acbdef67 + gz_bridge true-rpm hook (SITL as S168 pre-test), freeze params
`g5_freeze_s157/params.params`, matched GNSS 110 ms, SIM_GZ_ESC_FB=2, profiles D-NOISE-PROF (quiet/typ/harsh).
Fly: `bench/gate_g4.sh fly results/g4_gate_s169`; score (Docker): `bench/gate_g4.sh score results/g4_gate_s169`
-> `g4_table.md` (key1 `bench/g4_metrics.py`, keyed S168, A-52 closed S169). Acro row: not yet flown (RC168).
Windows from run.json events (hover: hold + 5 s .. end, cruise: traj + 3 s .. end), ulog time base.

Metric rows (GATES 4 limits; cruise = hover limit x1.5): all 18 runs PASS R20, R4, C20, clip with >= 10x margin.
Largest: cruise_harsh C20 0.0015 (limit 0.018), R4 0.77 % (limit 9 %); hover_harsh R20 0.034 % (limit 3 %). Seed
spread <= 15 %. Truth rotor speed (esc_status inst 1) in every run. A-53 (rpm stream gaps) bound holds (>= 30x).

Additional clause (harsh hover, `bench/g3_checks.py`, UNKEYED, g3_checks.json per run):
- G3 item 1 (LOC) PASS 3/3 (tilt max 1.5-1.6 deg). Item 2 on p, q, r, position: no sustained oscillation 3/3.
- Item 3 PASS 3/3: horizontal RMS 0.037-0.045 m (<= 0.15), altitude mean -0.008..0.051 m (<= 0.10).
- Command chatter (20-100 Hz, peak > 20 x median): FAIL 3/3 as written. 70.00 Hz line, amplitude linear in vibration
  (typ 9.3e-5, harsh 2.5e-4 RMS = 0.18 % of hover command), absent in quiet. PID reference (results/a54_s169,
  stock params, harsh hover s1): same 70.00 Hz line, peak/median 78, RMS 9.8e-5 -> not INDI-specific (A-54).
S171 (D-G3-SPAN, item 2 over the whole flight incl. descent): item 2 FAIL 1/3 harsh (harsh_s2 sustained 2 Hz q in the
AUTO_LAND descent, both keys; A-56: INDI descent rate RMS 3-6 deg/s harsh vs PID 0.3).
G4 verdict (S173, superseding "NOT YET"): metric rows PASS 18/18 (>= 10x margin, also 9/9 at D-JFF-SOURCE and 3/3
harsh at D-JFF-OFFB, results/g4_jff_s172, g4_jffoffb_s172). Additional clause:
- item 2 (whole flight, D-G3-SPAN): open FAIL 1/3 harsh (A-56, ~2 Hz p/q, no LOC, tilt < 11 deg); persists with
  rate FF removed in land (aa4fd2654a), so FF is not the cause. Cause search continues on the outer-loop
  measured-acceleration path (RC173).
- chatter: as written FAIL 9/9 runs in every profile, quiet included, both keys (a55_key1_all.md, g3_key2.md); PID
  carries the same 70 Hz line. Under Q14 option A (absolute floor of one DShot step) PASS: largest line RMS 2.5e-4
  < 5e-4. Owner answer pending (Q14); counted FAIL until then.
G4 is therefore NOT PASSED: A-56 (INDI-specific) and the chatter clause (stack-independent, Q14) both open.
