# Route check 143 (written for S144)

Read: STATE.md, GATES.md (5b), ANOMALIES.md (no A18 entry found), DECISIONS.md tail, JOURNAL.md tail 6,
results/g5_events_s142/README.md, results/g5_g55_s141_a18/lag_cause_s142.md, route_check_138.md.

## 1. Still on the shortest path?
Partly. G5 is the active gate and each session moved a row, but G5.5 has taken S139-S142 (4 sessions) on one
row (o1-o4/o7) and the lag chase is now the longest single detour of stage 5. G5.1-G5.4 are probes only, G5.7 fails
2/3, G5.6/5.8-5.11 are unflown. The G5.5 limit stays untouched (correct), but the fix path is open-ended.

## 2. Which decision is the difficulty a consequence of?
D-F7-GROUND/D-outer-arch chose accel_only stock PositionControl feeding the INDI stage, with A18 (jerk -> omega_ff) as a
side channel; the residual lag is that stock-chain a_c plus a jerk obtained by differencing a 30 ms offboard stream
(D-A18-REOPEN: setpoint jerk is 0 in the bench stream). Second root: the set-up fault (GNSS delay 0 vs EKF 110 ms) in
every G5 probe before S140, which hid the real lag for 3 sessions.

## 3. What a fresh start would do differently
Take jerk from the trajectory source (trajectory_setpoint.jerk, AUTO already fills it; make the offboard runner send
it, as a real planner does) instead of differencing; feed omega_ff and attitude setpoint from one aligned signal; and
verify the sim set-up (GNSS delay, stream period) with a matched pre-test before any gate probe.

## 4. Process rules
- Gate-progress lines: present in S140/S141 JOURNAL entries; S142 line not seen in the last 6 lines (check it exists).
- Cause-search budget: the S142 search used its budget with ~30-50 ms "unresolved"; STATE now adds A143b (lag chain
  split), i.e. a second cause search. Allowed only as the single evidence feed for the D-A18-SOURCE entry, one session.
- Probes vs evidence: G5.5 rows are probes (RC113) and are re-flown at freeze; no verdict of the o1-o4/o7 limit is
  needed now. A18 is not in ANOMALIES.md (tracked in DECISIONS only): add a line if it stays open.

## 5. Gate items moved since RC138
G5.1 6/6, G5.2 6/6, G5.3 hold 3/3 and mission 3/3 (probes); G5.4 9/9 (S135); Q7 closed (rule A); G5.5 scored
(o5/o6/offb PASS, o1-o4/o7 FAIL, 1.36 -> 0.59-0.79 m after A18); G5.7 official FAIL 2/3 (tilt err 5.2 vs 5 deg);
events injector built (G1.5 timing and two rows not injectable). G2-G4, G6-G8 unchanged.

## 6. Drop or defer (STATE Next actions)
- Cut item 0b/0c text to one line each (history in JOURNAL); STATE is at 7.9 kB of 8 kB.
- Fold A143b into the D-A18-SOURCE decision: no separate lag-chain report; first action is trajectory_setpoint.jerk
  on offboard (runner sends analytic jerk), re-fly o1/o2 once. If < 0.5 m, o3/o4/o7 follow; if not, record FAIL as a
  finding and move on (no more lag chasing before G5 completes).
- Defer item 3b (G5.7 PID comparison) behind the events rows unless G5.7 is the last open row; 4b, 4c, 5 stay deferred.
- Defer G5.9/G5.11 (EKF reset not injectable) and G5.6 maybe_landed pending Q8; fly kill, RC/link/offboard loss.
- Do not fix the ekf_yaw injector defect and failsafe-onset 2 Hz question until the events flight is the next row.

## S142 injector findings
The 3-24 ms lateness is a property of the lockstep runner tick, not a defect: the honest route is to log the applied
time (already logged), and report applied-minus-commanded per event against an owner-approved amended G1.5 for
MAVLink-side events (e.g. "within one runner tick, applied time logged"), via Q8, rather than build a 1.25 ms
injector. For maybe_landed and EKF z reset, record "not testable without firmware hooks" as an explicit gap in G5.6/G5.11
(or substitute the nearest injectable proxy: land-detector via real landing, horizontal reset only) and have the owner
accept it in Q8. Never relabel a MAVLink event as satisfying the 1.25 ms text.
