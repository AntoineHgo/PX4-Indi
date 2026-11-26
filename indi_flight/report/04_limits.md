Status: draft

# Chapter 4. Limits

This chapter states what the INDI (incremental nonlinear dynamic inversion) rate and acceleration controllers do not yet achieve. It rests on the gate evidence of chapter 3 and copies its numbers. Citations as in chapter 3: `GATES.md` = `indi_flight/GATES.md` (section title in quotes), `GS` = `indi_flight/GATE_STATUS.tsv`, paths relative to `indi_flight/`. All results are for one simulated airframe (quad5in, 5-inch, about 600 g). LOC = loss of control.

## 4.1 Robustness limits (G3)

G3 is NOT PASSED, final (owner answer Q35 A, `GATES.md` "Owner amendment S243"). Two failures are specific to INDI: PID flown on the same draw and seed does not fail them.

Draw 3 (route B, slow motors, motor time constant x2.4-2.8 of nominal): the INDI pitch-rate (q) signal oscillates sustainedly at 2.00 Hz on both scoring keys, reproduced at simulation speed 1. The local q power-spectrum peak is at 2.0-2.25 Hz, about 30 dB above PID. PID passes the oscillation item on this draw (`results/g3_routeB_s239/REF_S241.md`; `GATES.md` "Owner amendment S243").

Draw 264 (corner C3: thrust scale 0.351, motor 3 at 0.709, mass 1.3): saturation plus a weak motor. INDI tilts past 60 deg at the fault, both in freeze-10 (60.67 s at speed 4, 60.91 s at speed 1, ACT_TC 0.033) and in the re-fly with drawn controller ACT_TC 0.0177. PID flies the same draw without LOC (tilt max 40 deg). Changing ACT_TC (the actuator time-constant parameter) does not change the outcome (`GATES.md` "G3 verdict, re-fly with drawn controller ACT_TC (S213...)"). The cause was not traced to its origin.

Other INDI-affecting facts from the same campaign:
- S199 campaign, 300/300 flown: item 1 (no LOC) failed on run 245 (C1, 2 Hz pitch divergence) and run 264; item 2 (no sustained oscillation) failed on 79 of 297 scored runs; item 3 (steady state) 94.95 % (`GATES.md` "G3 verdict at freeze-10 (S199...)").
- Item 4 (lemniscate tracking, limit 0.5 m), draws 0, 2, 3 (INDI / PID): 0.418 / 0.768, 0.834 / 0.862, 0.553 / 0.917 m. PID fails too and INDI is not worse, so under the PID guard (Q35 C) these rows are a test defect and are not counted against INDI. One flight per stack and draw, so there is no spread estimate (`GATES.md` "Owner amendment S243").

Candidate fixes in the rate loop, each flown on its own build and not part of any shipped firmware, all missed the pass line on both keys: (i) ACT_BLD 0.10 (264 items 1 and 2, 262 item 2); (ii) MAP_TC 0.2 (LOC on the joint draw and on 264); (iii) rate integrator (LOC on 264, item 2 on 262) (`GS` row G3; `results/g3_cand_i_s231/`, `g3_cand_ii_s233/`, `g3_cand_iii_s235/SCORES.md`).

Hypothesis, UNVERIFIED: the draw 3 mode comes from actuator-model mismatch (motor tau x2.4-2.8 of nominal against MC_INDI_ACT_TC 0.033) (`GATES.md` "Owner amendment S243"). No evidence file shows it, and it does not explain draw 264, which does not depend on ACT_TC.

What a user should take from this. The operating envelope of the INDI controllers is not demonstrated for plants with motors much slower than the ACT_TC setting, nor for deep thrust saturation with one weak motor. On such plants INDI can fail where PID does not. No firmware after freeze-10 has a full 300-run result: the S213 re-fly stopped after 25 runs and route B after 3.

## 4.2 Un-identified start and identification (G6)

G6 is NOT PASSED (`GATES.md` "G6 item 7 verdict (S244...)"; `results/g6_item7_s212/TALLY_S244.md`). It requires G3, which is final NOT PASSED.

Item 7 flies the 60 corners C1-C6 un-identified (`MC_INDI_ID_OK` 0, gains x0.5, ACT_TC 0.05). Result: 6 LOC in 58 valid-or-counted runs. LOC in runs 278 and 295 (both keys); runs 262, 264, 269 and 292 were stopped by the flight watchdog and count as LOC. Runs 274 and 284 are invalid (harness) and were not re-flown. Over the whole run, item 2 fails in 21 / 22 of 54 scored runs (keys 1 / 2); overall pass is 12/54 on both keys.

Consequence for defaults. With `MC_INDI_ID_OK` 0 the controller flies un-identified values, and that start is not safe on all plant corners. Decision (DECISIONS D-ID-OK-LIMIT): arming is allowed un-identified, because the controller flies its own identification manoeuvre, and the limit is reported to the user: the un-identified state is for the identification flight on a healthy vehicle (full battery, no weak motor, calm air), not a flight configuration over the robustness plant range.

Identification quality, where measured: ACT_TC identification error 0 of 30 cells failed in the SITL grid (time constants within 3.7 %, delay offset about +1.75 ms); quad5in plant only, mostly one seed (`results/actc_grid_s209/README.md`).

Not covered:
- The roughly 100 Latin-hypercube un-identified runs were dropped (Q29), so coverage between the corners is not tested.
- The 10 wrong-start identification runs (G2, G3, G5 per start) were not flown; `bench/gate_g6.sh start_id` does not exist.
- Item 2 limited to the identification-manoeuvre window was not scored separately.
- Outlook airframes (stock x500, about 1 kg, one above 5 kg) have not been flown; nothing is reported for them.

## 4.3 Untested modes and rows (G5, G2)

G5 and G2 are PASSED at freeze-10 with the following rows not tested or only partly evidenced (`GATES.md` "G5 verdict at freeze-10 (S198...)", "G2 verdict at freeze-10 (S194...)"):
- G5.6 and G5.11 z reset: not tested (owner decision Q8(b), S175).
- Accel-only offboard, and take-off on an offboard setpoint alone: not tested (owner decision F-8).
- G5.10 saturation part: dropped (Q21): no stack reaches 4 motors >= 0.99 for 1 s. Saturated behaviour is therefore not covered by G5; see also 4.1.
- G5.3 mission and G5.4 RTL (return to launch) have key 1 only (no key-2 script); mission waypoint margin 0.03 m (worst 0.970 m against 1.0 m).
- G2 evidence limits: key 2 BLOCKED on 3 cells (both keys above the limits in each); rate and attitude spot margins thin (+1.9 / +3.0 deg); 3 rate cross-check groups and A-51 (model cross-check disagreement, bounded, all measured cells pass); 250 Hz controller rate not measured.
- Open anomalies that touch flight behaviour (`ANOMALIES.md`): A-4 INDI sensitivity to simulation speed (every INDI result is at speed 4 unless stated; G1.6 equality is PID only); A-6 outer-loop hover command excess below 30 Hz, cause unknown; A-50 and A-51 model versus measured margins; A-53 truth rotor-speed stream gaps; A-54 70 Hz motor-command line; A-57 frozen-eRPM detector trips 0.075 s after the hook; A-58 78 Hz motor-command line in 13 of 17 INDI position runs (a G4 matter, not G3 item 2).

## 4.4 Implementation limits (G7 open items)

G7 is open (`GS` row G7; STATE.md next actions 3 to 5).
- `MC_INDI_ID_OK` 0 behaviour: reported limit, no refuse-to-arm (DECISIONS D-ID-OK-LIMIT, see 4.2).
- R1 (refuse to arm without eRPM telemetry) is not enforced by code; a missing or stale measurement gives a modelled fallback and arming is allowed. Open: enforce or reword R1.
- Flash: fmu-v6x overflows by 23.5 kB (fmu-v5x measured +64.9 kB). Open, goes to an upstream note.
- The position module reads `esc_status` instance 0 only, has no frozen or error-count check, and uses a 100 ms ESC age against 20 ms in the rate module. Open.
- Guard parameters `MC_INDI_ERPM_TO`, `ERPM_FRZ`, `SP_TO`, `DT_MAX` have no flown test of their own (only the A-57 probe touched the frozen detector). Open, "justify in writing".
- Dead path: the `K_pos`/`K_vel` cascade in the acceleration control is unused (module always accel-only, `McIndiPosControl.cpp:315`). Open: remove after review or justify.
- The g510 LOC checker uses one sample, stricter than the 0.2 s in GATES (`results/g7_checkers_s215/README.md`). Open: justify or align.
- `MC_INDI_ACT_TC` yaml still says "round up", which D-OWNER-Q27 overturned. Open (parameter pass).
- Production boards do not build the modules; only the SITL board enables them (`report/DOCS_DRAFT_S201.md` item 4).
- Whole-branch F-10 review, unit 9 renames and the branch build check (g) are not done.

## 4.5 Simulation-only evidence

No real flight log exists. Telemetry (0-3 frames of 1.25 ms), actuator latency and DShot behaviour come from the simulator model; the real ESC firmware, telemetry driver and rates are not covered. The simulator eRPM-loss hook is late by 36-122 ms (A-57), so frozen and loss timings were not measured exactly. The simulated motor time constants are those of the model, so the 4.1 failures may differ on real motors in either direction. Chapter `report/06_bringup_checklist.md` lists the measurements before first flight; the ones that bear on these limits are:
- 6.3 Bench checks: motor time constant and telemetry latency and rate, to decide whether the plant lies inside the 4.1 failing region.
- 6.2 Parameters and guards referenced: the unevidenced guards of 4.4.
- 6.4 First hover sequence: start tethered or at low risk, since un-identified start (4.2) and saturation (4.1) are not demonstrated.
- 6.5 Identification steps run by the user: the identification must complete before `MC_INDI_ID_OK` is set.
- 6.6 Limits of this validation: overlaps this chapter.

## Unverified

- The statement that the 2 Hz pitch mode is INDI-specific rests on one PID flight per draw and seed (`REF_S241.md`); no spread estimate. [open: single flight]
- The actuator-model mismatch hypothesis. [open: unverified hypothesis]
- "6 LOC in 58" counts four watchdog stops as LOC per the chain tally; the per-corner split was not reported (no run-to-corner map). [open: no map]
- The 4.3 anomaly list is one-line summaries from `ANOMALIES.md` headlines; the full OPEN status of each (closing tests) was not re-read, and the list may be incomplete. [open: not re-read]
- Whether motor-time-constant and telemetry-latency measurements in chapter 6 map to the 4.1 failing region was inferred from the chapter headings only; the checklist body was not read. [open: headings only]
- The fmu-v5x flash figure is from S195 (`results/g7_s195/FORMAT_SIZE`), before later firmware commits; not re-measured. [open: stale number]
