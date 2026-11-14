# INDI project state

## Status summary (read this first)

- **Phase:** 6 starting (tuning frozen in session 13: D-freeze); also open: 1 (state of the art) 8 of 12 notes; phase 2 (PX4 analysis) started;
  phase 3 runner v0 works (pymavlink, seeded gz, one command per run).
  Benchmark spec frozen (`bench/scenarios.md` v1) before any INDI code.
  Phase 3 smoke test PASSED: `px4_sitl_default` builds in Docker and
  `gz_x500` flies headless (takeoff, hover at 2.5 m, land) at speed factor 1
  and 4 (4x: 43 s of sim in ~10 s wall, no log dropouts).
- **Headline results:** INDI (untuned defaults) flies in gz_x500: hover
  and roll step stable, no faults (`results/first_flight_indi_v0.md`,
  1 seed, smoke only). Roll step slower than default PID (rate rms 0.108 vs
  0.084 rad/s), off-axis coupling lower. Not a benchmark result yet. Sim speed 4 is
  equivalent to speed 1 for attitude/rate metrics but NOT for hover position
  rms (0.027 vs 0.064 m): position scenarios run at speed 1 (DECISIONS D-speed).
- **Session 7 findings:** INDI filters are synchronised (lag 0-1 cycle);
  in-loop G1 roll/pitch 237/245 (agree, R^2 0.95), yaw 7.4 (v0 default 30).
  INDI v0 hover motor-rate effort is 8x PID's, all of it from yaw: the yaw
  a_f noise passes to torque with gain 1/G1_Y. Fix decided (D-yawfilt), not
  yet implemented (`results/sync_check_v0.md`).
- **Session 8:** PID tuning r1 (240 flights): no candidate beats PX4
  default gains (`results/tuning/pid_r1.md`); hover reference ratio biased
  (~0.8 for all candidates: run-to-run noise, hover RMS varies 2x for the same seed). MC_INDI_YAW_CUT implemented; 10 Hz cuts
  INDI hover effort 7x (1.62 -> 0.23, PID 0.037) (`results/yawcut_check_s8.md`).
  INDI r1 (240 flights): best INDI tracks better than best PID on all 5
  tuning scenarios (ratios 0.67-0.98 vs 0.75-1.00) but J 1.17 vs 0.95
  because of motor-rate effort; PID wins r1 under the frozen cost
  (`results/tuning/indi_r1.md`).
- **Session 9:** untracked files triaged (raw logs ignored, metrics
  committed). Remaining INDI hover effort is yaw: yaw torque std 9x PID
  (PID filters yaw torque at 2 Hz by default, INDI was at 10 Hz)
  (`results/effort_axes_s9.md`). Round 2 for both families launched (D-r2).
- **Session 10:** PID r2 (16 cand x 3 seeds): best J 0.958 vs re-flown
  defaults 0.964, inside noise: PX4 defaults are the retuned PID baseline
  (64 candidates over r1+r2, `results/tuning/r2.md`). Gust and payload
  disturbance scenarios (T6, T7) implemented and flown once with PID.
- **INDI r2:** best J 1.150 (r1 1.167): tracks 12-18 % better than PID
  on hover/attitude/yaw steps, equal on rate pulses, but ~2.3x motor-rate
  effort; PID still wins under the frozen cost. Hover effort was the
  yaw path (yaw torque std 3x PID at YAW_CUT 4.6 Hz; roll/pitch equal).
- **Session 11:** c11 with YAW_CUT matched to PID (2 Hz): tracking
  unchanged, hover effort still ~2.1x PID. Remaining yaw chatter is gyro
  noise in nu = K_Y(r_sp - r) (gain K_Y/G1_Y ~ 0.8 vs PID P 0.2 behind a
  2 Hz filter) (`results/tuning/r2f_yc2.md`). Fix decided (D-yawnu: YAW_CUT
  also filters the yaw rate in nu): implemented (d2fb64330f, 17/17
  gtests). Hover check: INDI motor-rate effort 0.041-0.043 vs PID 0.037
  (~1.1x, was ~2.1x), yaw torque chatter gone (`results/yawnu_check_s11.md`).
  Tuning-set score with it: J 1.197 (PID 0.96): hover penalty gone, but
  step_yaw transient effort is ~7x PID and now carries the penalty
  (`results/tuning/r2f_yawnu.md`). PID still wins under the frozen cost.
- **Session 12:** step_yaw effort cause confirmed (`bench/yaw_step_effort.py`):
  INDI setpoint term K_Y*r_sp/G1_Y peaks at 2.75, yaw torque saturates at 1.0
  on every step (PID peak 0.33); INDI yaw loop tuned ~4x faster than PID
  (K_Y 5.8 vs P*G1 1.5 rad/s). INDI round 3 launched centred at K_Y 3,
  YAW_P 4 (D-r3). r3 c00 J 1.157, c01 1.087 (PID 0.96), running.
  Held-out scenarios H6 step_diag, H2 gust_diag, H3 com_shift implemented
  and flown once with PID (harness check only, `bench/scenarios.md` log).
- **Session 13:** r3 done (`results/tuning/r3.md`): best INDI c13 J 1.055
  vs PID 0.96; tracks better than PID on 4/5 tuning scenarios with equal or
  lower effort except step_yaw (~5x PID motor-rate effort, ~0.17 of J). Cause:
  the yaw setpoint step passes unfiltered into the torque increment, PID smooths
  it with its default 2 Hz yaw torque filter. D-yawsp: YAW_CUT now filters the
  yaw rate error, setpoint included (99634a6b71, 18/18 gtests). PID T8
  motor_loss_0 seeds 1-3 flown (consistent, yaw rms ~9 deg).
  c13 re-scored with D-yawsp: step_yaw effort 5.2x -> 1.42x PID, but yaw
  tracking 0.88 -> 1.06 x PID; J 1.058 unchanged because hover term is noise
  (D-hovernoise: sporadic vertical excursions for both families, horizontal
  hover RMS equal; `results/tuning/r3f_yawsp.md`). r4 yaw-only sweep (72 flights,
  `results/tuning/r4.md`): with D-yawsp no INDI yaw set beats PID on step_yaw at
  acceptable effort (best 1.089 x PID at 1.13x effort, c10); yaw near-parity is
  structural. Same params+seeds gave hover 0.77 vs 1.31: hover noise confirmed.
  r4f (c13 + r4 yaw) J 0.978 vs PID 0.96: tie within noise; INDI better on
  roll/pitch steps (0.88/0.93), equal on rate step and hover, worse on yaw
  (1.10). FROZEN as INDI tuned (D-freeze, `results/tuning/r4f.md`).
  First untuned scenario, T8 motor loss (3 seeds each): INDI roll/pitch RMS
  0.08/0.15 deg vs PID 0.71/0.68 (5-9x better), yaw 10.3 vs 9.0 deg, saturation
  12 % vs 7.5 % (`results/t8_motor_loss_s13.md`).
- **Session 14:** held-out + disturbance set, 5 seeds each (`results/heldout_s14.md`):
  INDI attitude RMS lower than PID on every disturbance scenario, 5/5 seeds: com_shift 0.15x, gust_diag 0.57x,
  gust_x 0.61x, payload_add 0.75x, inertia mismatch 0.88x, diagonal steps 0.92x; T8 fault-onset peak tilt
  1.6 vs 5.1 deg. Yaw worse whenever yaw is commanded (step_diag 1.30x). Effort equal except gust_diag 1.18x,
  inertia mismatch 1.26x. 10 seeds: attitude RMS lower 10/10, p=0.002 on all 6 (H2 44 %, H3 84 %, H6 10 % borderline); acceptance needs H1, H4, H5 still unflown.
- **Session 15:** H5 mismatch_combined (10 seeds, `results/heldout_h5_s15.md`): INDI LOSES. Roll-rate RMS 3.9x PID
  (step pattern) and 1.6x (rate pulses), effort 3.1x, from a 5-7 Hz roll limit cycle. Diagnosed: motor time constant
  x2 alone causes it (inertia/mass alone do not); with MC_INDI_ACT_TC matched it vanishes. Actuator-model mismatch is
  INDI's main robustness weakness here. Trajectory mode + T5/H1/H4 implemented; 10-seed batch flying.
- **Acceptance (session 15, `results/acceptance_s15.md`): all 6 H scenarios flown, 10 seeds. Outcome under the
  frozen rules: "INDI does not outperform PID".** Criterion 3 fails on H5 (rate pulses 1.58x, ACT_TC-mismatch limit
  cycle); criterion 1 fails on H4 (both controllers crash 10/10, alike up to impact). Criterion 4 met (hover effort 1.04x). Criterion 2 met (H1, H2, H3; H6
  at threshold). INDI's strength: disturbance rejection; its weakness: actuator-model mismatch.
  T5 lemniscate: INDI 0.95x position RMS; H1 fast circle 0.73x (infeasible for both) (`results/heldout_s15.md`).
- **Session 17:** ACT_TC sweep (post-acceptance, 21 runs, `results/act_tc_sweep_s17.md`): MC_INDI_ACT_TC 0.33x-3x on
  the stock plant gives NO limit cycle (roll-rate RMS 0.129-0.161, graded). The H5 limit cycle needs a physically
  slower actuator the model does not know; ratio alone does not explain it (D-actsweep assumption falsified).
- **Session 19:** review s1/s3/s5 committed; its top bug (yaw filters zeroed every landed cycle) fixed post-freeze
  (1d776dc6dc, 19/19 gtests, D-landyaw); check re-fly: metric windows unchanged within noise (`results/landyaw_check_s19.md`). Review s5 explains the ACT_TC sweep: model slower than
  plant is a gain reduction (safe); dangerous case is plant slower than model, band-pass boost at 1/(2 pi sqrt(tau_e tau_t)).
- **Blocker:** none. Usage budget is the binding constraint.
- **Caveat on notes:** paper notes are from PDF text extraction; several
  equations are flagged as reconstructed. Check them against the PDFs before
  quoting in the report.
- **Last updated:** 2026-11-14, session 21 (review triaged, G2_Y bound fix, figures, ch. 2 draft). Before that: session 20. Before that: session 16 (ch. 8 draft + control-law review in flight). Before that: session 15 (H1/H4/H5 implemented, batches flying). Before that: session 13. Before that: session 11. Before that: session 10. Before that: session 7. Before that: 2026-11-13, session 5 (architecture written; INDI law
  library + unit tests committed, not yet wired into mc_rate_control; first
  G1 identification: pitch 211 (R^2 0.90), roll 321 (R^2 0.63), yaw not
  identified; see `results/identification_g1_v0.md`).

## Phase checklist

| # | Phase | Status |
|---|-------|--------|
| 1 | State of the art (`research/`, report ch. 2-3) | in progress: reading list written, notes smeur2016, acquatella2017, blaha2024, wang2019, tal2021, impl_paparazzi, impl_px4_prior done; steffensen2023 (session 9); remaining: sieberling2010, sun2022, smeur2018, impl_indiflight |
| 2 | PX4 analysis and design (`plan/`, report ch. 4-5) | architecture v1 done (`plan/architecture.md`); ch. 4 drafted and integration analysis code-checked (session 9, `plan/px4_analysis_verification.md`: 44/54 confirmed, 2 corrected); ch. 5 not drafted |
| 3 | Simulation + benchmark harness on PID baseline (`docker/`, `bench/`) | image works, SITL build OK; gz_x500 headless smoke flight OK at speed 1 and 4 (`bench/smoke_gz.sh`); equivalence of results across speed factors not yet verified with metrics |
| 4 | Implementation (firmware + unit tests) | not started |
| 5 | Tuning and iteration | not started |
| 6 | Validation and report | not started |

## In progress

- SESSION 22 (2026-11-14): DONE figures referenced in ch. 8 (Fig 8.1-8.3) and ch. 9 (Fig 9.1), review s5 band-pass
  mechanism + triaged review risks (a-i) added to ch. 9 (0a1ca5a2a5). IN FLIGHT: (M) sonnet drafts
  `report/01_introduction.md` + `report/10_conclusion.md`; (N) haiku drafts `report/11_appendix_reproduce.md`.
  If cut off: check those files, relaunch only for what is missing.

- SESSION 21 (2026-11-14) DONE: review complete + triaged (28eba44030, items 8-13 + triage in its Summary);
  MC_INDI_G2_Y max 100 -> 1 (2bb0ba3ac9, SITL build OK; DT_MAX min 0.01 and K min 1 already guard review item 11
  at param level); (K) `bench/make_figures.py` + 4 figures (f7ea7940b7, ab392e193e; ratios match md tables
  within 2 %; README notes: bars are medians of per-seed ratios, traj effort ratios and motor_loss_0 10-seed
  reference not in any md; host python needs plain `python3`, not `-I`); (L) ch. 2 drafted (3855 words, trim).
  Ch. 2 open: sources.md lacks keys smeur2018, wang2019, steffensen2023 (add); 8 [TO VERIFY] (smeur2016 rotor
  eqs, acquatella PI constants, smeur2018 Table 1 / gain conflict, wang Monte Carlo, Paparazzi adaptation scaling,
  PX4 forum 'can not take off' quote vs impl_px4_prior reading) and 5 [GAP] (sieberling2010, sun2022/UZH,
  tal2021 identification, modelled actuator state, indiflight code).
  NEXT (cheap first): 3 keys added to sources.md (wang2019, steffensen2023 URLs still missing: find via title search); reference the figures in ch. 8 (fig_attitude_ratio,
  fig_effort_ratio, fig_rate_timeseries) and ch. 9 (fig_act_tc_sweep); add review limitations (triage list) to
  ch. 9; then ch. 1 intro, ch. 10 conclusion, bibliography, appendix reproduce (one sonnet agent each, <= $0.5);
  REPORT FIXES list (session 14 entry); PDF build if pandoc is in the image.

- SESSION 20 (2026-11-14): review section 2 committed (4f1abbd426). IN FLIGHT: (J) fable fills sections 4 and 6
  of `review/control_law_review_s16.md` (replaces 'Not covered in this pass.'); if cut off, relaunch only for what is missing,
  then add their items to the Summary and triage remaining findings into fix / report-limitation.

- SESSION 19: (G) DONE ch. 3 drafted (~4500 words, trim; [TO VERIFY] smeur2016 eqs 7,9,10,22-27, acquatella2017 eqs 4,26,28, wang2019 eq 13; [UNSOURCED] normalised G1, up/down asymmetry; cites [review_s16], add to sources.md; f* peak (tt-te)/(tt+te) checked by orchestrator); (H) fable fills review
  sections 2, 4, 6 + summary in `review/control_law_review_s16.md`; (I) DONE landed-yaw check (`results/landyaw_check_s19.md`, unchanged within noise); was log
  `results/landyaw_check_s19.log` (ends CHECK_DONE; resumable: re-run the header's two run_batch.sh calls), output
  `results/landyaw_check_s19/{step_diag,com_shift}/indi_tuned/seed{1,2,3}[_x4]/metrics.json`. NEXT: compare with
  `results/runs/{step_diag,com_shift}/indi_tuned/seed1-3` (summarize_seeds.py), write `results/landyaw_check_s19.md`,
  commit metrics. If partial, relaunch agents only for what their files lack. Remaining review findings to triage:
  s1 dt-jitter redesign resets t_f (hardware risk), stale allocator status at 400 Hz, maybe_landed P-only law.

- SESSION 18 (2026-11-14) IN FLIGHT: review file still only a skeleton (2 fable runs cut off). Relaunched smaller:
  (E) fable reviews sections 1, 3, 5 only of `review/control_law_review_s16.md` (writes each section as done);
  (F) sonnet drafts report ch. 6 simulation environment -> `report/06_simulation.md`.
  If partial next session, relaunch only for what the files lack; sections 2, 4, 6 of the review remain.
  (F) DONE ad8e7a8e41: ch. 6 drafted (~2850 words, trim). Open [TO VERIFY] in it: lockstep config source, motor-loss
  allocator awareness, latency not characterised, gz aero plugins, hover excursions vs speed factor.
- SESSION 17 (2026-11-14) IN FLIGHT: session-16 review (B) was cut off with only its section skeleton on disk, ch. 8
  draft (A) was committed (2cd1c49235). Relaunched: (B') fable control-law review -> `review/control_law_review_s16.md`
  (fills the skeleton section by section); (C) sonnet drafts report ch. 9 discussion -> `report/09_discussion.md`.
  If partial next session, relaunch only for the missing sections.
  (C) DONE: ch. 9 drafted (~3700 words, trim to ~3000). Open [TO VERIFY] markers in it: full T-set re-tune done?;
  gz motor tau 0.0125 up / 0.025 down (unchecked); CA_ROTOR_KM 0.05 vs gz 0.016 effect on yaw G1/PID; bench/sim_fidelity.md
  missing (noise/bias/latency undocumented: write it); INDI speed 1 vs 4 check; PID candidate count 64 vs 40 (ch. 9 uses 40);
  flight modes covered.
  Ch. 9 open checks resolved session 17: gz motor tau 0.0125/0.025 verified (model.sdf); sim_fidelity.md written
  (gz k_m/k_f 0.016 vs CA_ROTOR_KM 0.05 recorded there). Still open in ch. 9: full T-set re-tune, KM effect on yaw,
  INDI speed 1 vs 4, flight modes covered. PID count settled: 40 (fixed in r2.md, DECISIONS, ch. 9; ch. 7 l.136
  'Inconsistencies' item 1 still to update).
  (D) DONE + committed 702e9f3787 (`results/act_tc_sweep_s17.md`). Optional follow-up: plant-tau sweep via
  model_variant.py key tau (~21 runs) to map the real stability boundary.
  (B'') fable review relaunched session 17 (order 1,3,5,2,4,6, writes each section as it goes): if partial, relaunch
  for missing sections only.
  (old D) ACT_TC sweep (D-actsweep), 21 runs, `results/act_tc_sweep_s17/run.sh`, log `sweep.log`
  (ends with SWEEP_DONE; runs with metrics.json are skipped, so re-run run.sh if incomplete). Output
  `results/runs/step_roll/indi_act<f>/seed<N>_x4/`. NEXT: table of roll-rate RMS / effort / saturation vs 1/f
  (summarize_seeds.py), look for the limit-cycle onset ratio, write `results/act_tc_sweep_s17.md`, commit metrics.
- SESSION 16 (2026-11-14) IN FLIGHT: (A) sonnet drafts report ch. 8 results -> `report/08_results.md`;
  (B) fable independent review of the INDI control law -> `review/control_law_review_s16.md`. If a file is
  partial or missing next session, relaunch only for what it lacks. Committed bd5da68490 (re-flown PID hover seeds 1-3).
  Known: gust_x and payload_add pid_default seed1 `disturbance_trigger.json` modified on disk (onset differs from the
  committed one, metrics.json unchanged): a re-run overwrote it; not committed, check before quoting seed 1 onset.
- SESSION 15 DONE: H1/H4/H5 flown and committed, acceptance decided (negative, see summary). NEXT (phase 6):
  (1) metrics.py: end the window at ground contact for crash-capable scenarios, re-score H4/T8; move the session-15
  inline trajectory/H4 table scripts into `bench/` (reproducibility); (2) T1 hover effort, frozen candidates, 10 seeds: DONE (1.04x, met)
  (criterion 4); (3) report ch. 8 results + ch. 9 discussion (delegate drafts to sonnet from results/*.md:
  heldout_s14, heldout_s15, heldout_h5_s15, acceptance_s15, t8_motor_loss_s13, tuning/*.md); (4) fable review of the
  control law and of the conclusions; (5) the open REPORT FIXES list below. Optional, clearly labelled as
  post-acceptance work and never retro-fitted into the verdict: ACT_TC robustness sweep (INDI stability margin vs
  motor time-constant error), which the H5 finding motivates.
- (old) SESSION 15 RUNNING (detached): H5 batch (`results/h5_s15.log`, mismatch_combined_att/_rate, speed 4, seeds 1-10,
  both controllers), then trajectory batch (`results/traj_s15.log`: traj_lemniscate T5, traj_circle_fast H1,
  motor_loss_2 H4, speed 1, seeds 1-10). Runs with metrics.json are skipped, so re-run the log-header commands if
  incomplete. NEXT: `bench/summarize_seeds.py` on each (trajectory block for T5/H1/H4: rms_3d_m; ground contact for
  H4 = min altitude in window ~0), write `results/heldout_s15.md`, decide acceptance, commit metrics/run.json.
  H5 DONE and committed (34b68de63e). Smoke (PID seed 1): H1 3.3 m RMS (infeasible, tilt limit), H4 PID touched the ground (D-h5).
- SESSION 14 DONE: held-out seeds 1-10 committed (`results/heldout_s14.md`, Wilcoxon in `bench/summarize_seeds.py`).
  NEXT: (1) check `bench/scenarios.md` for H1, H4, H5 definitions and implement/fly them (10 seeds, both
  controllers) to decide acceptance: H1 traj_circle_fast, H4 motor_loss_2 (motor 2 x0.6 during
  T5 lemniscate), H5 mismatch_combined (inertia x0.8, mass x1.15, motor tau x2; T2+T4) per `bench/scenarios.md` l.72-76;
  (2) T8 motor loss seeds 4-10 DONE and metrics committed (`results/t8_s14.log`): summarise with
  summarize_seeds.py motor_loss_0 (metrics.json motor_fault block too), commit metrics/run.json; (3) T1 hover effort ratio for criterion 4;
  (4) report ch. 8 results (delegate draft to sonnet from results/*.md); (5) independent fable review of the control law.
  REPORT FIXES TO DO (from drafting agents): (a) architecture.md out of date vs code (no K_ff/setpoint derivative, no 20 ms freshness, landed output = G1^-1(nu - a_f) with t_f held 0, yaw filters missing): update plan or note in ch. 5; (b) ch. 5 G2 yaw derivation is the agent's own: verify before final; (c) PID candidate count: D-freeze/r2.md say 64, rounds sum to 40 (24+16): fix DECISIONS; INDI flights ~600 vs 792-852 counted; (d) PID hover effort 0.037 (yawcut_check_s8) vs 0.054 (effort_axes_s9) same scenario/seed: explain; (e) PID J quoted 0.946/0.958/0.964/0.96: pick one reference (re-flown defaults) for the report; (f) scenarios.md promised full-T re-tune: not done, state it in ch. 7 or do it; (g) ch. 5 is 5400 words, fine.
- RUNNING end of session 13 (detached, ~30-40 min): held-out/disturbance batch,
  PID defaults + INDI tuned, seeds 1-5: speed 1 {com_shift gust_diag gust_x
  payload_add}, speed 4 {step_diag mismatch_inertia}. Log
  `results/heldout_s13.log` (header lists the 4 run_batch.sh calls; runs with
  existing metrics.json are skipped, so re-run them if incomplete). Output
  `results/runs/<scenario>/{pid_default,indi_tuned}/seed*/`. NEXT: compare per
  scenario (mean/std over seeds), commit metrics.json/run.json.
- NEXT: phase 6 on frozen candidates (PID defaults vs
  INDI tuned = `results/tuning/indi/r4f/c00/params`). (1) T8: run
  `bench/disturbance.py` for peak tilt/recovery at fault onset, find where INDI
  saturates. (2) Held-out set (H2 gust_diag, H3 com_shift, H6 step_diag, H5?) and
  T6 gust, T7 payload, T9 inertia mismatch, >= 5 seeds per controller, CPU-only
  batches via run_batch.sh (PARAMS_FILE absolute path, CONTROLLERS=indi_tuned).
  (3) Report hover with horizontal/vertical split (D-hovernoise). (4) Then report
  chapters 5-9 (delegate drafts to sonnet from results/*.md and DECISIONS.md).
- DONE session 13: r4f + D-freeze (553c4dbdd0); INDI T8 seeds 1-3.
- DONE session 13: r4 (`results/tuning/r4.md`, ec2bd1ad7a).
- DONE session 13: c13 D-yawsp re-score (`results/tuning/r3f_yawsp.md`).

- r3 FINISHED (16/16, `results/tuning/indi/r3/`); best: `[tune] c13 done: J=1.0552 failures=0`.
  NEXT: write `results/tuning/r3.md` (J vs PID 0.96, effort ratios,
  `bench/yaw_step_effort.py` on best step_yaw), commit r3 metrics. Queued PID
  T8 batch never started (waiter matched its own pgrep pattern): run
  `results/t8_pid_s12.log` command by hand without the loop. Never use
  `pkill -f`/`pgrep -f` with a pattern that appears in the caller's command.

- QUEUED session 12: after r3 ends, PID T8 motor_loss_0 seeds 1-3 (speed 1,
  log `results/t8_pid_s12.log`, output `results/runs/motor_loss_0/pid_default/`).
  INDI T8 waits for the r3 best candidate.
- DONE session 12 (sonnet agent, ~$0.26, 12 calls): T9 `mismatch_inertia`
  (1eec3f211b, 8f77dd79b8): `bench/model_variant.py` builds a per-run x500
  copy (keys ixx, iyy, izz, mass, tau; tau/mass untested), spawned via
  PX4_GZ_MODELS; gz reports Ixx 0.0282 vs stock 0.0217 (verified), stock runs
  unaffected. PID seed 1 x4: roll RMS 3.27 deg vs stock 3.35, rise 0.411 vs
  0.424 s: x1.3 inertia barely shows in PID's attitude tracking (only roll-rate
  RMS 0.096 vs 0.086). Log `plan/t9_model_variant_log.md`. Open: does H5 scale izz.

- RUNNING session 12 (detached): INDI r3 (D-r3), 16 cand x 5 scen x 3 seeds,
  ~240 flights, ~1.5 h. Log `results/tuning/r3.log` (header = command,
  resumable), output `results/tuning/indi/r3/summary.csv`. Next session: if
  no `px4-indi-*` container runs and summary lacks candidates, re-run the
  header command; then write `results/tuning/r3.md` (compare J with PID 0.96,
  per-scenario effort ratios, step_yaw effort with `bench/yaw_step_effort.py`).

- DONE session 11: r2f_yawnu scored (J 1.197, `results/tuning/r2f_yawnu.md`).
- DONE session 11: T8 motor_loss_0 (f3205105bd): runtime SIM_GZ_EC_MIN1/MAX1 x sqrt(0.7) (thrust x0.70), attitude mode, then +45 deg yaw step; PID seed 1: motor 0 0.73 -> 0.905, saturated 1.5 s, peak tilt 5.1 deg, altitude sags 1.2 m (attitude mode, fixed thrust; identical for both controllers). Notes `plan/t8_motor_loss_log.md`.
- DONE session 11: D-yawnu implemented (d2fb64330f firmware+3 gtests, 17/17 pass, SITL build OK; 5cbf7478fc param doc; diff reviewed by orchestrator). Hover check flying: c11+YAW_CUT 2 seeds 1-3 -> `results/yawnu_check_s11/hover/seed*/`, log `results/yawnu_check_s11.log` (untracked); if no metrics, re-run the command recorded in `results/yawnu_check_s11.md` or STATE next actions.
- DONE session 11 (`results/tuning/r2f_yc2.md`): `python3 bench/tune.py --family indi --round-name r2f_yc2 --n-candidates 1 --seeds 1 2 3 --jobs 6 --sampler-seed 0 --span-factor 1.0 --base-params bench/params/indi_v1.params --center bench/params/indi_c11_yc2.json` (c11 with YAW_CUT 2 Hz, 15 flights), log `results/tuning/r2f_yc2.log`. Resumable: re-run if summary.csv missing.
- Nothing running. r2 finished and committed (`results/tuning/r2.md`).
- DONE session 10: T6 gust_x + T7 payload_add (D-dist, commits 160dda984d,
  4681575174); PID-default seed 1: gust 0.61 m / 14.2 deg / recovery 15.9 s,
  payload 0.35 m / recovery 4.8 s. Unverified: wrench not read back from gz
  (inferred from response), speed > 1 untested. Injector uses the one-step
  `/wrench` topic each 4 ms tick (`/wrench/persistent` accumulates, crashed gz).
- Session 9 (2026-11-14): tuning round 2 (D-r2) launched detached, PID then
  INDI, 16 candidates x 5 scenarios x seeds 1 2 3 each (~480 flights,
  ~2-3 h). Log `results/tuning/r2.log`, outputs
  `results/tuning/{pid,indi}/r2/summary.csv`. Next session: if no
  `px4-indi-*` container runs and a summary lacks candidates, re-run the
  command in the log header (resumable). Then write `results/tuning/r2.md`.
- Nothing running. Session 8 finished PID r1 and INDI r1.
- Session 7 (2026-11-14): PID tuning round 1 launched detached at the end
  of the session: `python3 bench/tune.py --family pid --round-name r1
  --n-candidates 24 --seeds 1 2 --jobs 6 --sampler-seed 0`, log
  `results/tuning/pid_r1.log`, output `results/tuning/pid/r1/summary.csv`.
  ~250 flights, ~1 h. Next session: check `docker ps` for `px4-indi-*`; if
  it is not running and summary.csv lacks candidates, re-run the same
  command (resumable). tune.py and the spec are committed; smoke rounds
  in `results/tuning/{pid,indi}/smoke` (untracked). Smoke: re-flying
  pid_default gave J 1.016 at one seed, so ~2 % is run-to-run noise.
- Nothing in flight. Session 6: INDI wired into mc_rate_control
  (d66f114963 msg `indi_rate_status`, d6182aea41 `MC_RATE_CTL_TYPE` +
  `MC_INDI_*` params). SITL build OK, lib gtest OK, diff reviewed by the
  orchestrator. INDI has NOT flown yet. Log: `plan/integration_log.md`.
  rate_ctrl_status is not published on the INDI branch (by design).

## Next concrete actions

00. Session 11 next steps: (a0) NEXT: on step_yaw seed 1 of
   `results/tuning/indi/r2f_yawnu/c00`, quantify nu_y/G1, yaw torque and
   motor spread around the step to confirm that the unfiltered setpoint
   path causes the 7x effort (CPU+few tokens); then INDI round 3 under the
   D-yawnu firmware (centre `bench/params/indi_c11_yc2.json`, span 1.5, 16
   cand x 3 seeds, round-name r3; say the YAW_CUT semantics changed). Any
   setpoint pre-filter must be offered to PID too (fairness). Also re-fly PID on
   T8 motor_loss_0 seeds 1-3 and INDI likewise. (a) DONE D-yawnu; DONE check hover effort with `bench/indi_terms.py`
   and `bench/effort_axes.py` on c11 + YAW_CUT 2 (expect yaw drms ~0); then
   an INDI round 3 (new YAW_CUT semantics, say so) on the 5 tuning
   scenarios x 3 seeds; (b) T8 result: see `plan/t8_motor_loss_log.md`;
   then T9/H5, T5/H1, H2/H3 one small sonnet task each.
0. Session 10 next steps: (a) DONE INDI r2 analysis; (a2) NEXT: INDI c11
   with MC_INDI_YAW_CUT=2 (PID's yaw torque cut) on the 5 tuning scenarios x
   3 seeds (CPU only, run_batch.sh with NAME_TAG); compare J and per-axis
   effort; if yaw still dominates, analyse why a matched cut-off does not
   match PID (yaw G1 7.4 small -> 1/G1 noise gain); (b) remaining sim
   extensions, one small sonnet task each: T8 motor loss (per-channel
   SIM_GZ_EC_MAX at runtime, check thrust ~ omega^2 so scale by sqrt),
   T9/H5 model variants (generated x500_base override on GZ_SIM_RESOURCE_PATH),
   T5/H1 trajectories, H2/H3 profiles in disturbance.py. Sonnet agents
   overrun the 30-call target (59 calls, ~$0.9): split tasks smaller.
   Session 9 next steps: (a) DONE INDI r1 analysis; (b) DONE: hover position RMS is not
   repeatable per seed (re-fly up to 2.2x the reference, `pid_r1.md`
   follow-up): find the non-determinism, then >= 8 hover seeds in J; (c) DONE (session 9): remaining INDI hover effort is yaw
   (`results/effort_axes_s9.md`); (d) LAUNCHED session 9: round 2 for both families (D-r2).
   Use NAME_TAG for parallel run_batch.sh calls (container names collide).
   Session 7 next steps (done except d): (a) DONE tune.py committed;
   (b) LAUNCHED (see "In progress") PID tuning round 1 on T1-T4
   (`--family pid --n-candidates 24 --seeds 1 2 --jobs 6`, add
   MC_YAW_TQ_CUTOFF to the PID space per D-yawfilt) — CPU only;
   (c) implement `MC_INDI_YAW_CUT` (D-yawfilt) in the INDI lib + gtest
   (brief ready for one sonnet agent: `plan/yawfilt_spec.md`),
   rebuild, re-check hover effort with indi_v1.params; (d) INDI tuning round
   1 with the same budget (add MC_INDI_YAW_CUT to the INDI space).
   Primary metric of T2/T3 is stepped-axis attitude RMS, not IAE (metrics.py
   has no IAE): record this in the scenarios.md change log before tuning.
1. Phase 2 architecture DONE (`plan/architecture.md`, D-arch-1..6).
   INDI library DONE and integrated in mc_rate_control (session 6).
   First INDI flights DONE (session 6). Next: plot indi_rate_status
   (t_f vs allocated torque, a_f vs nu) on step_roll to check filter
   synchronisation before any gain change; then K sweep on T-set. Before tuning: SITL step
   identification of G1, actuator tc, loop/gyro rate (architecture sec. 10).
2. Harness: find why hover position rms differs at speed 4; add the
   remaining scenarios of `bench/scenarios.md` to `bench/scenarios.py`
   (trajectory, wind/gust, payload, degraded motor, plant mismatch: these
   need simulator extensions in separate commits).
3. PID retuned baseline (documented tuning effort) before INDI flies.
4. Remaining phase-1 notes: sieberling2010 (fetch), steffensen2023 (PDF on
   disk), sun2022 (fetch), impl_indiflight (code on disk).
5. Budget lesson: two Sonnet code-reading agents (~30 tool calls each) cost
   about $1 together. Use at most one Sonnet agent per $3 session.

## Key findings so far (from notes, to verify before the report)

- With a fixed effectiveness, rate-loop INDI is algebraically an incremental
  PI(D) with gain 1/(G*Ts) (acquatella2017, eq. 29-30). Any INDI advantage
  over a well-tuned PID must come from effectiveness scaling, actuator-state
  feedback (true motor state vs commanded), saturation handling, or the
  acceleration feedback path: the benchmark must be designed to probe these.
- Paparazzi: same 2nd-order Butterworth on gyro and on modelled actuator
  state; first-order actuator model; WLS allocation with roll/pitch priority
  in the full version; no NaN checks, fixed dt (impl_paparazzi).
- wang2019: INDI's model-error perturbation is (B-B^)Δu, shrinking with
  sampling, vs (B-B^)u for NDI: "less sensitive", not model-independent.
  No transferable numeric bound for a multicopter rate loop.
- tal2021: outer loop is PD + INDI increments; motor speed from optical
  encoders, 2nd-order Butterworth 30 Hz on motor speed and IMU; no PID
  baseline in hardware. Without motor feedback a motor model is needed (our
  inference).
- Prior PX4 PR #25216 was closed by the stale bot; reviewers wanted a
  separate module and no changes to commander/ControlAllocator
  (impl_px4_prior).

- PX4 integration facts (plan/px4_analysis_integration.md, unverified by a
  second reader): allocator is linear in motor command, normalised torque,
  sequential desaturation (thrust > roll/pitch > yaw); Gazebo
  `esc_status.esc_rpm` only echoes the command (no measured rotor speed), so
  SITL INDI needs an onboard first-order motor model; x500 motor time
  constants 0.0125 s up / 0.025 s down; PX4 CA_ROTOR_KM 0.05 vs gz
  momentConstant 0.016 (built-in yaw model mismatch). Suggested selection
  pattern: enum param in mc_rate_control (default PID), INDI law in a new
  lib beside src/lib/rate_control; mc_nn_control/mc_raptor use external
  modes and are not a suitable pattern.
- smeur2018: wind tunnel 10 m/s, INDI 0.21 m vs PID 1.51 m position error,
  but the PID had no gain matching (caveat for our fair-baseline design).

## Known problems

- RESOLVED (session 7): roll vs pitch G1 (321 vs 211) was an artefact of the
  open-loop fit; in-loop fit gives 237/245 (D-g1-v1).
- INDI yaw noise amplification (D-yawfilt) open; and step_yaw INDI v0
  saturates motors 14 % of the time (vs 4 % PID).
- INDI library: on a non-finite input it resets the actuator model to zero,
  so the next valid cycle starts from t_f = 0 (torque transient). Acceptable
  for stage 1; revisit (hold last valid state) during module integration.
- DONE: `make tests TESTFILTER=indi_rate_control` (ASAN build) passed in
  session 5 (log `results/unittest_asan_s5.log`, untracked).
- Guard false positives: both Sonnet agents had a heredoc/python shell
  command blocked as "system administration"; they used the Edit tool
  instead. Brief agents to write files with Write/Edit, not heredocs.

- **Session 1 lost its work to a usage limit.** Five Sonnet subagents ran in
  parallel for about 14 minutes, took the 5-hour usage window from 11 % to
  101 %, and were all killed by HTTP 429 before writing anything to
  `research/`. They were too broad (100-140 tool calls each) and kept
  everything in context until the end. The prompt now asks for small tasks
  that write as they go.
- **Budget, measured:** one 5-hour window holds about $9 of model usage; that
  session used 6 % of the weekly window. Plan for a few hours of active agent
  time per week.
- **Raw material already on disk** (gitignored, moved from `/tmp`):
  `research/raw/` holds shallow clones of paparazzi, indiflight (+ support),
  crazyflie-firmware, ActiveSetCtlAlloc, lei-ss/indi, and partial PDF and text
  downloads in `foundations/`, `robustness/`, `papers_dl/`, `px4_eco/`. The
  folder names come from the killed agents; check contents before relying on
  them.

## Conventions (so a fresh session does not have to rediscover them)

- Commits: conventional format, no `-s` sign-off (the owner has not reviewed
  the work), trailer `Assisted-by: Claude:<model id of this session>` (the
  orchestrator now runs on `claude-opus-5-5`), no `Co-Authored-By`. Push with
  `git push origin feat/indi-control`.
- Everything that builds or simulates goes through `indi_project/docker/run.sh`.
- Containers started by this project are named `px4-indi-*`. The container
  `peaceful_bhabha` (image `px4io/px4-dev:v1.16.0-rc1-...`) belongs to the
  owner: never stop or remove it.
- The shell guard rejects any command containing the bare words `apt`, `dpkg`,
  `snap`, `halt`, `reboot`... even as grep patterns; phrase commands around that.
  It also rejects `gh auth`.
- `Tools/simulation/jmavsim/` and `nohup.out` are untracked files that predate
  the project: leave them alone and never `git add -A`.

## Ledger (rough)

| Session | Subagents spawned | Simulation runs | Notes |
|---------|-------------------|-----------------|-------|
| 1 (2026-11-13) | 5 (all killed by usage limit) | 0 | ~$10 spent, only the Docker image survived; host was also suspended 7 h |
| 2 (2026-11-13) | 5 (4 haiku, 1 sonnet), all completed | 1 SITL build, 4 smoke flights (2 OK) | ~$2.5 of $3 cap |
| 3 (2026-11-13) | 1 sonnet (runner v0), haiku notes | ~6 runner test flights | runner left uncommitted, committed in session 4 |
| 4 (2026-11-13) | 2 sonnet, 1 haiku | 18 runs (speed check), 0 failures | ~$3 cap |
| 5 (2026-11-13) | 1 sonnet (INDI lib, 27 tool calls) | 2 runs (step_pitch, step_yaw PID seed1), 0 failures | ~$2.4 used of $3 cap |
| 7 (2026-11-14) | 1 sonnet (tune.py, 16 tool calls) | 2 INDI runs + 4 smoke tuning flights; PID tuning r1 (~250 flights) left running detached | ~$2.4 of $3 cap |
| 8 (2026-11-14) | 1 sonnet (yaw cutoff, 14 tool calls) | 1 SITL build, 6 check flights (2 tooling failures), PID r1 finished (240), INDI r1 finished (240, 0 failures) | ~$1.8 of $2.61 |
| 9 (2026-11-14) | 1 haiku (steffensen2023), 1 sonnet (ch. 4 draft) | round 2 launched (~480 flights) | triage + yaw effort analysis |
| 10 (2026-11-14) | 1 sonnet (disturbance injector, 59 tool calls, ~$0.9) | 2 test flights; r2 finished (480 flights, 0 failures) | ~$2.6 of $3 |
| 11 (2026-11-14) | 2 sonnet (T8 motor loss 14 calls; D-yawnu 13 calls) | 15 INDI (r2f_yc2) + 1 T8 PID + 3 hover (yawnu), 0 failures; r2f_yawnu (15) left running | yaw effort root cause and fix, ~$2.4 of $3 |
| 13 (2026-11-14) | 0 | 3 T8 PID, 15 INDI r3f_yawsp, 72 INDI r4, 15 INDI r4f, 3 INDI T8, 1 SITL build, unit tests | r3 analysis, D-yawsp, D-hovernoise, D-r4; ~$2 of $3 |
| 6 (2026-11-13) | 1 sonnet (module integration, 29 tool calls, ~$0.45) | 1 SITL build, 2 INDI runs (hover, step_roll seed1), 0 failures | $1.63 cap |

## Journal

- 2026-11-13: session 1 started from scratch; created `STATE.md`, `DECISIONS.md`,
  Docker image `px4-indi-sim`. Cut off by the 5-hour usage limit at 08:13.
- 2026-11-13: owner review after session 1: supervisor now on Opus 5.5 with a
  per-session spend cap, max 3 concurrent subagents, host kept awake; prompt
  updated (small tasks, write as you go, bounded phase 1, early smoke test).
- 2026-11-13: session 2: committed Docker image files; SITL build OK in Docker; reading list; notes smeur2016, acquatella2017, impl_paparazzi, impl_px4_prior; smoke flight script `bench/smoke_gz.sh`; smoke flight OK at speed 1 and 4.
- 2026-11-13: session 3: froze `bench/scenarios.md` v1 (T1-T9 tuning, H1-H6 held-out, paired Wilcoxon acceptance); notes wang2019, tal2021.
- 2026-11-13: session 2 closed: note blaha2024 added (RLS effectiveness identification, no PID baseline in that paper).
- 2026-11-13: session 4: committed runner v0; analyses plan/px4_analysis_{rate,integration}.md; note smeur2018; speed-factor check (18 runs): speed 4 OK for attitude/rate, not for hover position; PX4 rate-path analysis.
- 2026-11-13: session 5: `plan/architecture.md` + D-arch-1..6; gz x500 IMU 250 Hz, rotor inertia noted; `bench/identify_g1.py` and `results/identification_g1_v0.md` (roll only); INDI library delegated.
- 2026-11-13: session 5 closed: INDI law library + 10 gtests committed; pitch/yaw identification added.
- 2026-11-13: session 6: INDI selectable in mc_rate_control via MC_RATE_CTL_TYPE (PID default), indi_rate_status message; not yet flown.
- 2026-11-13: session 6: first INDI flights (hover, step_roll) stable with default parameters.
- 2026-11-14: session 7: `bench/check_sync.py`; INDI filters synchronised; in-loop G1 241/241/7.4 (`indi_v1.params`); yaw noise path found (D-yawfilt); tuning driver spec + agent.
- 2026-11-14: session 8: PID r1 done (defaults best of 24); MC_INDI_YAW_CUT (lib, gtests, param); yaw cut 10 Hz cuts INDI hover effort 7x; INDI r1 launched.
- 2026-11-14: session 8: INDI r1 done: better tracking on all tuning scenarios, worse J from effort.
- 2026-11-14: session 9: untracked files triaged; INDI hover effort traced to yaw; tuning round 2 (both families, 3 seeds) launched.
- 2026-11-14: session 9: Steffensen 2023 note; report ch. 4 draft + code verification of the integration analysis (SIH has a first-order motor lag SIH_T_TAU and a modelled esc_rpm, unlike gz).
- 2026-11-14: session 10: PID r2 done (defaults within noise of best); T6 gust_x and T7 payload_add scenarios added (ApplyLinkWrench injector).
- 2026-11-14: session 10: INDI r2 done (J 1.150 vs PID 0.958; effort from yaw path persists).
- 2026-11-14: session 11: YAW_CUT 2 Hz control run: effort unchanged; yaw chatter traced to gyro noise in nu; D-yawnu decided.
- 2026-11-14: session 11: T8 motor_loss_0 scenario added; D-yawnu implemented: INDI hover effort ~1.1x PID (was ~2.1x).
- 2026-11-14: session 11: D-yawnu scored on tuning set: J 1.197 vs PID 0.96, penalty now from step_yaw effort (~7x PID).
- 2026-11-14: session 13: r3 scored (c13 J 1.055 vs PID 0.96, step_yaw effort the only penalty); D-yawsp implemented; PID T8 seeds 1-3 flown.
- 2026-11-14: session 13: D-yawsp scored (yaw effort fixed, yaw tracking lost, J 1.058); hover term found noise-dominated; r4 yaw sweep launched.
- 2026-11-14: session 13: r4 done (yaw parity with PID is structural under D-yawsp); r4f combined candidate launched.
- 2026-11-14: session 13: r4f J 0.978 (tie with PID); INDI frozen (D-freeze); T8 motor loss: INDI roll/pitch 5-9x better, yaw worse.
- 2026-11-14: session 14: T8 fault-onset metrics; report ch. 5 and ch. 7 drafted (sonnet, 2 agents); held-out seeds 1-5 done (INDI better on all disturbance scenarios, yaw worse when commanded); seeds 6-10 done: INDI attitude better p=0.002 on all 6 scenarios.
- 2026-11-14 session 15: H5 implemented and flown (10 seeds): INDI loses, ACT_TC-mismatch limit cycle diagnosed; trajectory mode + T5/H1/H4 added, batch launched.
- 2026-11-14 session 15: T5/H1/H4 flown (10 seeds); acceptance decided: INDI does not outperform PID (H5 criterion 3, H4 criterion 1).
- 2026-11-14 session 19: landed yaw-filter bug fixed (D-landyaw); review s1/3/5 committed; ch. 3 + review s2/4/6 + fix check in flight.
- 2026-11-14 session 18: ch. 6 simulation drafted; ch. 7 PID count item resolved; fable review (sections 1,3,5) relaunched.
- 2026-11-14 session 17: ACT_TC sweep summarised (no limit cycle from model error alone); fable control-law review relaunched.
- 2026-11-14 session 21: review complete and triaged; MC_INDI_G2_Y bounded; figure script + 4 figures; ch. 2 drafted.
