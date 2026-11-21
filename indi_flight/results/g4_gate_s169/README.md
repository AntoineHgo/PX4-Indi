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
G4 verdict: NOT YET. Metric rows PASS; chatter clause FAIL pending A-54 (suspected simulator alias of the 1P/2P
vibration line) and key2 of g3_checks.py.
