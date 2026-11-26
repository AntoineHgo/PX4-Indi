# Solver brief, G3 step (c) candidates (ii)/(iii) (written S232, fixed before any (ii)/(iii) code)

Launch: one agent, model opus, effort high (GATES "Owner amendment S225": one solver run). Needs a fresh session
budget (~$5); split into 3 parts below, each part ends with files on disk so a cut loses at most one part.
First line of the brief: `Purpose: build and fly G3 rate-loop candidates (ii)/(iii) against the fixed pass line.`

## Fixed inputs
- Pass line: DECISIONS.md D-RATE-BLD-2 "S226 ACTIVE" (never edited). Candidate (i) MISSED (results/g3_cand_i_s231/
  SCORES.md): 264 item 1 exc 5.35 m + item 2 p/q/r sustained; 262 item 2 q sustained (baseline passes); 283 item 2 q
  worse on key 1. Its flight chain + score.sh are the template for (ii)/(iii) flights.
- Cause context (read only these): results/g3_refly_actc_s212/restore264/falsifier_s222/README.md,
  restore264 INVESTIGATION_A/_B, ref264_s224. Draw 264: weak motor 0.709 + saturation, trim grows with collective.
- Order: (ii) first. (iii) only if (ii) misses a flight cell. Simplest passing wins.
- (ii) per-motor slow correction of the command-to-omega^2 map from measured rotor speed (multiplicative, bounded,
  frozen when landed, on telemetry loss/frozen, and while the allocator saturates that motor; reset at arming).
- (iii) bounded rate integrator on the INDI increment with allocator-saturation anti-windup, frozen when landed,
  reset at arming.
- Each candidate's parameter values are written in its README BEFORE its first flight; no sweeps, no item2_split,
  no 2 Hz cause search, no tb change (ACT_BLD stays at the FREEZE-10 value 1.0).

## Build rule (D-BINARY-GZFIX, STATE action -1)
- Never touch build/px4_sitl_default or the gate binary 903eae63. Candidate binary = gate sources (c0b733e677
  firmware files + GZBridge fix f110361a33) + the candidate diff only, built in a worktree OUTSIDE the repo
  (e.g. ~/px4_cand_ii), in docker image px4-indi-sim, its own build dir; record sha256 and the source diff.
- Code meets F-10 (MISSION). Unit tests for the candidate in src/lib/indi_rate_control (weak-motor loop,
  anti-windup, landed, telemetry loss/frozen, arming reset), each break-checked once. Firmware is committed to
  feat/indi-flight only if the candidate wins (port the diff onto HEAD then, behaviour-neutral naming).

## Parts
1. Design note (one page, design/cand_ii_design.md) + code + unit tests + candidate binary. Done = tests pass,
   binary sha recorded, README in results/g3_cand_ii_s2xx/.
2. Four pass-line flights (joint, 264, 262, 283) with the cand_i chain.sh pattern, run_in_background, --speed 1,
   base params g5_freeze_s157, candidate binary; score.sh (both keys); SCORES.md with the pass-line verdict.
   The orchestrator may hand part 2 to a sonnet/medium agent.
3. Only if all flight cells pass: G2 rate cells (roll/pitch/yaw, 800/400 Hz, measured + model-only, 2 seeds) and
   G2-STEP 9/9 on the candidate binary. Then (d) independent review (opus, high), then (e).
If (ii) misses: same parts for (iii). If (iii) misses: route B (GATES "Owner amendment S225"), no new question.
