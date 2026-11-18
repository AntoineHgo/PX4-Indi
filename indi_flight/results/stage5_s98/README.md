# P98 stage 5 pre-test: thrust gap 0.85 with firmware c32d022f9e (D-ALTCTL-Z), seed 1, speed 4, --sim v2

Build: existing build/px4_sitl_default (binary 10:08:16; no src file of mc_indi_pos_control / indi_accel_control newer than it, so not rebuilt).
Params: `gap.params` (= stage5_s70/gap.params, MC_INDI_POS_EN 1, CA_R_W_MAX 2700). Flights sequential through indi_project/docker/run.sh (`fly.sh`).
Scenario added to bench/scenarios.py: `s5_gap085_altctl` (mode stick, no "stick" segment so sticks stay neutral; settle 15 / up 5 / hold 40;
motor_fault at "up", motors 0-3 x0.85). The runner applies motor_fault in stick mode without change (run.json motor_fault events).
s5_gap_check.py works unchanged on the stick run (hold z from run.json hold_pos_ned, truth z).

Command (A): `indi_project/docker/run.sh -n s98a -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario s5_gap085 --controller indi_s98 --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/stage5_s98/gap.params --out indi_flight/results/stage5_s98/A_gap085/run`
(B) same with `--scenario s5_gap085_altctl --stick-mode altctl --out .../B_altctl/run`; (C) B with `gap_at.params` (gap.params + MC_INDI_EN 1, MC_AT_EN 1), `--out .../C_altctl_at/run`, `-n s98c`.
Checks: `pretest_gate.py <run>/flight.ulg <dir>/gate.md`; `s5_gap_check.py <run>`.

| flight | gate | z err [ev+10,ev+20] mean/std | last 10 s | max abs dev | settle (|err|<0.05) | note |
|---|---|---|---|---|---|---|
| A s5_gap085 offboard pos | FAIL (rate RMS ax0 0.0242, ax1 0.0225 >= 0.02) | 0.003 / 0.023 | -0.043 / 0.024 | 0.091 | ~3 s after event, then +-0.05 wander | stage 0x7f; mean_u valid 1.0 |
| B s5_gap085_altctl ALTCTL | FAIL (0.0244, 0.0223) | 0.035 / 0.014 | 0.036 / 0.011 | 0.203 (peak 0.16 at ev+3 s) | 5 s to 0.057, <0.05 from ~ev+8..12 s; 0.010-0.037 later | nav_state 1 (ALTCTL) seen in log |
| C B + MC_INDI_EN 1, MC_AT_EN 1 | FAIL (0.0224, 0.0206) | 0.027 / 0.017 | 0.025 / 0.011 | 0.161 | as B | px4.log "autotune disabled with INDI"; no start errors |

Prediction without gap compensation: 0.368 m. S70 reference for s5_gap085 (same params): 0.330 / 0.306 m standing, NOT removed.

## Findings
- A: the standing z error is gone (0.003 m at ev+10..20 vs 0.33 m in S70; max dev 0.091 vs 0.372). Collective thrust 0.1367 -> 0.1608 as in S70. Convergence is fast but not clean: last-10 s mean -0.043 m (above hold), std 0.024.
- B: ALTCTL with the gap: peak sag 0.16 m (~3 s after event), standing 0.025-0.036 m, i.e. about 10x below the 0.368 m prediction.
- Gate: all three FAIL only on rate RMS ~0.022-0.024 rad/s > 0.02. The gate is applied to a whole flight including the thrust step and ALTCTL; the S70 PASS was on the plain hover_gap flight, so this is not the same criterion basis (UNVERIFIED that FAIL is gap-induced; no hover-only regression flown here).
- Whether the z-only stage was active: NOT directly logged. indi_pos_status has no stage/z_only field; only "INDI stage cond" console messages (0x7f at flight, 0x7e/0x3e at the end of log) and mean_u_valid=1.0. nav_state 1 in B proves ALTCTL, z-only inferred from the improvement vs the expected PID-like sag, not observed.
- Single-key: seed 1 only, no repeat; the 0.01-0.04 m differences between A/B/C are not significant.
- C: MC_INDI_EN 1 echoed in px4.log; MC_AT_EN 1 not echoed (no "curr -> new" line) although the param exists (mc_autotune_attitude_control); "autotune disabled with INDI" is printed, so the autotune module declined by design. No start error.
- Untracked raw logs: A_gap085, B_altctl, C_altctl_at, *.stdout.txt (empty on success). Nothing committed; scenarios.py edited (s5_gap085_altctl).

S98 note: pretest_gate FAIL on A/B/C is a window artefact: its window [47, 77) s includes the motor fault at ~71 s; the step transient raises rate RMS. Key K98 over fault+10..20 s: body-rate RMS 0.001-0.006 rad/s.
