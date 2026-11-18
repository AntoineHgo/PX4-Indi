# T196 G2 report draft log
Output: indi_flight/report/g2_margins.md (preliminary, no gate verdict).
Sources read: GATES.md 103-176; results READMEs stage5_s82/s83/s84/s86/s87/s91 (+model_vs_measured.md), stage3_s53 pitch, s56 yaw, s57 roll/yaw, s57_pre, s76, s77_400, s77_a34, s78_a34; ANOMALIES A-30/34/35/36; DECISIONS D-G2-BREAK/INJ/PINJ; route_check_93; JOURNAL grep.
Not opened: ulog files, raw margins json, per-cell xy json (table taken from the s87 README), design/t195_att_outer_key.md and attitude_break_s86.md (cited via the results files only).
Not found: telemetry latency value; any measured PID margin; model-only at HEAD; measured-path 267 Hz rate; pitch measured path; yaw outer loop; second key for S91 margins and S86/S87 margins; model GM for the rate-loop cells.
Derived numbers: delay margin in periods (DM / period) in 2.1, marked derived.
Flags: A-34 (S57 vs HEAD rate PM 77.5 vs 69.1); S86 z GM "nan" vs S87 xy GM 18-19 dB; s86 accel z 800 s2 PM 58.3 (first) vs 59.6 (re-fly); S84 pt1 PM 58.7 superseded by 61.3.
