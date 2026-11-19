# Route check 129 (S129)
Inputs: STATE.md, ANOMALIES.md (headings, parked rows only), DECISIONS.md tail (D-IDENT-STOP, D-DEFAULTS-FW),
JOURNAL tail S124-S128, RC126. No flights run. Code fact: mc_indi_pos_control is one 1107-line module, hover
slice (D-S5-SLICE) + ALTCTL z (D-ALTCTL-Z); no per-mode dispatch beyond that.

## 1. Still the shortest path?
Partly. G1 passed, G2-G8 open, and every open gate except G2 needs the stage-5 outer loop in every mode (G5 is
the outer loop itself; G3/G6/G7/G8 evidence for it needs MC_INDI_POS_EN=1, S118 note). Stage 5 had no new code
S122-S128 (7 sessions: stick pilot, ident, yaw A-43/A-44, defaults). S127-S128 are the second slip in a row
below the accuracy any gate asks for, but they are smaller than S125-S126: the defaults file was ordered by RC126,
and the ID_OK gate removed a real 5-8x loop-gain hazard on unidentified airframes. Total slip against RC126: 1 session.

## 2. Which decision?
D-IDENT (Q6 = B: INDI flies its own ident) again, through its "full gains gated by an ident-status parameter"
clause: it turned defaults into firmware work (D-DEFAULTS-FW). Second cause: the K127 MAJOR2 rule "key every
change, pretest every parameter" sent S128 into the ACT_TC 0.033 vs 0.05 flights, which changed nothing in
firmware (default stays 0.05). That pretest was not on any gate path.

## 3. Fresh start on stage 5 (and the defaults before it)
- Build the mode dispatch first (nav_state -> setpoint source -> stock library or INDI path) with one smoke
  flight per mode, then add gates, defaults and ident around a working multi-mode flyer.
- Defaults = derived values with a conservative gain scale from day one, one file, no pretest of values the
  firmware does not take.
- Gate list owned by the build list: each mode row names its G3/G5 cell, so no work item lacks a consumer.

## 4. Is the S127-S128 slip justified?
S127 and the ID_OK gate: yes (ordered by RC126, safety-relevant, small, keyed 0 BLOCKING). The ACT_TC pretest:
no (value not taken by firmware; quad5in-only file change). The slip is now closed: ident, defaults and gating
are done and nothing in stage 4 remains before G5. Owner-question trigger from RC126 ("no multi-mode code by
S129") is met on its letter. It is not raised now because S129 is this check plus the first mode, and
blocking on the owner would add a session. It is raised automatically at the end of S131 if any of the
modes below has no flown code. STOP list: yaw fit (A-44, V3), more ACT_TC/ident pretests, anomaly chases,
review-note reading, new keys on non-code artefacts.

## 5. Next 3 sessions
- S129: (a) 1 page design/g5_build_list.md: one row per mode (MANUAL/stabilized, ALTCTL, POSCTL, AUTO takeoff,
  loiter, mission, RTL, land, OFFBOARD, ACRO), columns nav_state, setpoint source, library used, status, smoke
  scenario, gate cell. (b) FIRST DELIVERABLE: POSCTL in McIndiPosControl with MC_INDI_POS_EN=1, SITL smoke
  flight on quad5in: hold 10 s, 2 m step via stick/trajectory setpoint, log in results/s5_posctl_s129, README
  with xy/z error and pass/fail. Commit code, list and result.
- S130: AUTO family (takeoff, loiter, mission 2 waypoints, RTL, land) via trajectory_setpoint, one smoke
  flight each in one session by scenario script; fix only what blocks a flight.
- S131: OFFBOARD (position + velocity setpoints), MANUAL/stabilized/ACRO pass-through check, then first G5
  probe over all modes (probe, not gate evidence, per RC113). Route check RC132: owner question if any mode
  row is not flown; otherwise proceed to G2 offline todo and G3/G5 batches with POS_EN=1.
