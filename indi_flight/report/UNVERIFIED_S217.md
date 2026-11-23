# Unverified items, S217 pass (chapter | item | outcome)

01 | margin numbers from g2_margins.md | open: needs re-scoring
01 | G3 C3 corner, mass 1.3 | open: waits Q31
01 | J_r / G2_Y 27 vs IV 163-166 | open: needs identification
01 | ACT_TC 0.033 vs rule | open: hardware; quad5in_indi_defaults.params:20 still UNVERIFIED
01 | MC_INDI_DELAY other IMU cutoffs | open: needs flight
01 | allocator saturation | open: stock allocator out of scope
01 | lower spot PM freeze-10 | open: needs cause search
01 | sensor filter orders | open: src/modules/sensors not read
01 | ID_OK in every flight | open: per-run check
01 | unit tests not read | open
01 | yaml ACT_TC text | corrected: citation module.yaml:127-128 -> mc_indi_rate_control_params.yaml:126-128 (text still "round up", default 0.05); open: waits G7 pass
03 | g2_margins tables | open
03 | G2 amendment text Q13/Q16/Q19 | closed: GATES.md:169,551,574,605,616
03 | G4 effort thresholds vs amendments | closed: GATES.md:351-360 PROPOSED table; S175/S183/S187 amendments (GATES.md:529-558,605-) change only chatter, item 2, Q20 guard
03 | G4 item 1/2 definitions | closed: GATES.md G4 "Additional" (items = G3 items 1-3; item 1 no LOC, item 2 no sustained oscillation, GATES.md:760-761)
03 | G5.11 limits | corrected: 0.12 deg / 0.248 m were measured worst values; limits excess <= 1 deg, excursion <= 0.5 m (results/freeze10_s193/G5_SCORES.md:160); chapter table rows edited, measured numbers unchanged
03 | G5.1-G5.7 audit vs S198 | open
03 | G5.10 PID values | closed: PID reference not re-flown at freeze-10, freeze-9 PID kept (G5_SCORES.md:185, G5_VERDICT_AUDIT.md:27)
03 | G1.1/G4 reproduce commands | open: results/freeze10_s193/g4_score.sh exists, not read
03 | g5_gaps_s198 path | closed: ls confirms results/freeze10_s193/g5_gaps_s198 only; chapter already uses F10/ path
03 | hole-rate numbers | open
06 | telemetry rate/latency/loop/CPU (B3,B4,B8) | open: needs flight/hardware
06 | esc_rpm tolerance, detector trip time | open: hardware
06 | DShot stale/zero erpm on loss | open: hardware (B6)
06 | second esc_status instance | open: real board
06 | guard params tuning | open: hardware
06 | ACT_TC yaml text, ident_actc on hardware | open: waits G7 pass (yaml unchanged); needs flight
06 | DSHOT_MOT_POL default | corrected: default 14 is the parameter default too (src/drivers/dshot/module.yaml:87); table row 29 edited; default line numbers still open
A | freeze numbers 1-5 | closed: no FREEZE-1..5 in DECISIONS.md, JOURNAL.md, STATE.md (grep)
A | stage 5-7 first sessions | open
A | Q8-Q15, Q17, Q18, Q21 answers | closed: DECISIONS.md:950-961, 1042, 1143-1147; row 98 text updated
A | LESSONS.md stage label | open: LESSONS.md:10 says "Stage 1", conflict stays
A | errata.md E-1 scope | closed: errata.md:12 confirms UNVERIFIED and only E-1 exists
A | re-scored with corrected metric | open
A | G1 first-test session | open
A | Q31 outcome | open: waits Q31
