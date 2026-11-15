# Subagent management audit (read-only), generated from logs/run-*.jsonl (62 files), supervisor.log, STATE.md, DECISIONS.md

## 1. Launch counts (extracted by script from Agent tool_use events; result records give total_cost_usd and subagent_stats)
- 62 jsonl files (59 supervisor "runs" completed + 3 early/failed). 63 Agent launches. Total cost (last result per file) = $156.18.
- By model: sonnet 40, haiku 15, fable 8, opus 0. Launches with missing model: 0 (rule "always pass model" respected 63/63).
- Orchestrator = claude-opus-5-5 ($111.82, 71.6%); sonnet subagents $26.53 (17.0%); fable $17.04 (10.9%, fable-5-1 14.25 + fable-5-2 2.80); haiku $0.79 (0.5%). Subagents total $44.4 (28%).
- Per-launch average: sonnet ~$0.66, fable ~$2.1, haiku ~$0.05.
- Launches in session 1: 5 sonnet (all failed, api_error/usage limit, $8.47, session ran 7.3 h). Tasks: broad research topics ("INDI foundations literature notes", "PX4 simulation model audit"), prompts 5.4-7.6k chars.
- Typical session cost $2.2-3.0 (cap $3 set by run_orchestrator.sh MAX_BUDGET_USD=3); median session 697 s; total wall 23.7 h over 59 supervised runs.
- Launch size (47 agents with usage record): tool_uses median 16, range 6-59; 6 agents exceeded 30 calls (32, 37, 37, 44, 45, 59: disturbance injector 59, mc_indi_rate_control module 44, actuator ident 30/ pos_control 32 ...). Mean 92k tokens each. So the "~30 tool calls" rule was largely respected.
- Concurrency (local_agent task_started/notification): max 5 in session 20261113-005309 (violates "max 3"; no refusal recorded, refused_concurrency_limit=0); 3 in three sessions; otherwise <=2. Parallel launches: 5 sessions launched 3+ agents in one message (005309:5, 225729:5 (3 concurrent), 230913:3, 232533:3, 013756:3).
- Foreground (blocking) launches: 10 (e.g. fable review 075946 launched foreground with only $1.49 cap left -> killed by budget).

## 2. Compliance / losses
- subagent_stats totals: spawned 63, completed 47, failed 5 (all session 1), killed by system 9, killed by parent 1. => 15/63 (24%) did not complete.
- Killed-by-session-end (lost-work risk) were mostly fable reviews: control-law review launched 6 times in s16-s20 (072509, 073233, 073838, 074523, 075222, 075946), file held only headings for 3 sessions (STATE.md ~856-895, "2 fable runs cut off"). Fable cost for that one review ~ $14+ (fable-5-1 $14.25). Also session 122235: both agents (sonnet figures + fable conclusions review) killed; 230913: runner v0 killed; 223703: watchdog replay killed.
- Relaunches of same task: control-law review x6 (relaunched smaller each time, "only what the file lacks" rule followed: order 1,3,5 then 2,4,6); session-1 five tasks relaunched as 5 smaller haiku/sonnet tasks in session 2.
- Too broad: session-1 five agents (each a whole literature/code-reading topic); control-law review (6 sections, whole law) as one fable agent; disturbance injector (59 calls, 660 s).
- Within-session pattern: orchestrator launches an agent, then ends session at cap with the agent still running (waiting-for-agent messages in 072509, 073233, 073838, 074523, 075222): cost of waiting small but fable work got killed at session end each time.

## 3. Verification
Examples of real verification:
- 20261115-013756: after sonnet "Implement IndiAccelControl library" the orchestrator re-ran the 18 gtests in Docker (`make tests TESTFILTER=IndiAccel`) and grep-checked omega_ff/t_c/a_f lines against spec.
- 20261114-075222: fable review found yaw-filter reset bug (DECISIONS.md:345); orchestrator checked it in code, wrote regression test that fails without fix/passes with it, re-flew step_diag/com_shift seeds 1-3.
- 20261114-223703, 151051, 175333, 171444, 033810: git show / git diff of the agent's commit before accepting.
- 20261113-225729 haiku notes: orchestrator mostly appended bibliography rows and did not read notes (accepted).
Accepted on summary / light checks:
- Chapter drafts (sonnet): after ch.8 (072509), ch.9 (073233), ch.3 (075222), ch.1/10 (112833) the orchestrator ran wc, grep for key numbers, git commit. Ch.9 was 3,700 words vs 2,000-3,000 target and had 7 [TO VERIFY]; ch.3 4,500 words and 3 [TO VERIFY]; deferral to later haiku checks (113647 ch.3 vs PDFs, 114354 ch.2 markers) -> review/ch3_equation_check_s23.md (8 equations; "Eq. (22) superscript the only correction", one citation fix "Eqs. 29-30 -> Eq. 29"), review/ch2_marker_check_s24.md (six sentences rewritten).
- haiku checks of sonnet drafts were scoped to marker lines only.
Metrics:
- bench/metrics.py v0 was written by a sonnet subagent (session 20261113-230913, tool_use parent toolu_01EEJ7JH..., model claude-sonnet-5-5) and validated by that same agent (its own RUNNER_NOTES.md "full validation"). Later edits by sonnet agents (disturbance_metrics s10, motor-loss/V' s46) and by the orchestrator (045-065914: nanmax fix, per-axis step metric). No agent or script ever recomputed a primary metric (attitude RMS / position RMS / effort) from raw ULogs independently as a cross-check. Orchestrator did ad-hoc pyulog scripts for diagnoses (e.g. 20261114-122235, 20261115-030346) but not as metric audits.
- First substantive metric error was found by the human owner, not by an agent: review/s8_owner_review.md finding 6 (attitude metric for INDI POS computed vs stale stock setpoint; later fixed d56a4e1ac1 "attitude metric from indi_pos_status q_d"). Owner also found accelerometer aliasing (hover att RMS 5.47 deg vs 0.33 deg), delay direction error, missing bias removal, fallback not levelling, FF after rate limits. All in code written by sonnet and accepted with passing gtests.
Reviews scope:
- report/review_s8.md (fable): scope = report sections vs results/s8n_oset.md, s8k_gnss_delay.md, DECISIONS D-s8-*, with "spot checks" in bench/disturbance.py, scenarios.py, s8p_hover_effort.sh, indi_accel_control.cpp. 2 major (payload 15% vs 25%; unsupported vibration mechanism) + 11 minor. It checks report vs results file; it does NOT recompute results from ULogs.
- review/conclusions_review_s25.md (fable): ch. 8-10 vs results/*.md (found 10-seed vs 3-seed T8 inconsistency).
- review/control_law_review_s16.md (fable): code read, "No code was edited, built or run" -> code only, no results.
- Neither review checked results-vs-raw-data.

## 4. Context cost / STATE.md
- STATE.md 130.8 KB (1291 lines, ~33-37k tokens at 3.5-4 chars/token); DECISIONS.md 77.6 KB (~20k tokens); ORCHESTRATOR_PROMPT.md 16 KB. STATE.md grew from 4.2 KB (first commit 11-13) to 131 KB over 210 commits touching it. STATE.md was read (Read or cat/sed/grep) in 61 of 62 sessions, ~6.5 read commands per session.
- Orchestrator made 2,496 API calls (deduped) at avg 77k context tokens (193M cache-read, 5.2M 1h-cache-creation, 1.6M output). If STATE.md is ~35k tokens at its final size, it is ~45% of the average per-call context at the end, probably 25-35% over the whole project. With list-price ratios (read 0.1x, 1h write 2x, output 5x input) cache reads are ~51% of opus cost ($57); STATE share thus plausibly $15-25 (10-16% of total). ESTIMATE, pricing ratios not verified.
- Split: orchestrator $111.8 (72%), subagents $44.4 (28%). Of the orchestrator's calls, 123/2,496 (5%) were explicit polling (sleep/until/ScheduleWakeup/Monitor).
- Ledger in STATE.md ("Ledger (rough)", line 1177) has 21 rows for 59 sessions, out of order, only sonnet/haiku/fable counts partly; end-of-journal lines ("Agents 0; runs 3") give per-session counts from s52 on. Rule "ledger of agents in STATE.md" only partially met.

## 5. Task type -> model
- haiku (15): paper notes (Smeur2016, Acquatella, Blaha, wang, tal, steffensen, smeur2018), PDF equation check, marker check, AM32 eRPM facts, ident G_T/k_cmd, hover mode log scan, reproduction appendix.
- sonnet (40): literature/code reading (session 1), PX4 analyses, benchmark runner v0 (+metrics.py), INDI lib, integration, tuning driver, yaw cutoff, disturbance injector, T8/T9 scenarios, D-yawnu, D-omega2, module mc_indi_rate_control, v3 blend, V' scenarios, stage-8 lib and module, ALL report chapter drafts (2,3,4,5,6,7,8,9, 1+10, stage-8 section 5.9), figure scripts.
- fable (8): only independent reviews (control law x6, conclusions review, stage-8 sections). Opus subagents: 0.
- Rework traced to subagent output: (a) yaw-filter reset bug in sonnet's yaw-cutoff implementation (s8 session 001651), found 8 sessions later by fable, forced firmware fix + re-flights (DECISIONS.md:345-350); (b) disturbance injector first flights failed physically (wrench accumulated each message; plan/impl_log_disturbance.md:13), fixed by the same agent; (c) stage-8 library/module accepted, then owner review found aliasing/delay/bias/fallback issues (but spec itself was by orchestrator); (d) ch.9 PID candidate count 64 vs 40 inconsistent (fixed 073838); chapter drafts left [TO VERIFY] (03: 3, 05: 1, 07: 1 still in report today) ; (e) metric attitude for INDI POS stale setpoint.
- NOT a cheap-model error: the stage-8 jerk feedforward draft with both signs wrong (DECISIONS.md:806) was the orchestrator's own design draft (plan/s8_outer_loop_design.md, committed by orchestrator session 6014c4f09a), caught by the orchestrator while writing the spec (session 013756) before the sonnet implementation was launched. Not a delegation failure; a point for self-derivation.
- spec deviations: plan/impl_log_v3_blend.md:16 test tolerance relaxed 1e-4 -> 1e-3; 013756 sonnet lib reimplemented bodyzToAttitude statically (deviations listed in return summary).

## 6. Idle / wasted spend
- Session 1: $8.47, 7.3 h wall, 5 agents failed, "only Docker image survived" (STATE ledger row 1).
- 20261114-075946: $1.49, 149 s, fable review launched foreground then killed by budget_exhausted (wasted).
- 20261114-202503: $3.30 over 7,271 s, ended by budget (error_max_budget_usd) while detached flights ran.
- 5 sessions <=330 s cost $6.94 (3.1 + 1.0 + 3.17 + 0.36 + 2.28 ... ); one api_error session $0.36 (175237); 003804 $0.56 (api_error).
- Waiting for fable review in 073838 (31 turns, $3.16) "rest of the session held for that review" = idle spend.
- Sessions per 5h headroom are consistent with cap, no systematic polling loop (5% of calls).
