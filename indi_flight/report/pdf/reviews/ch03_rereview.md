# Re-review of chapters/03_inner_loop.tex after fixes (commit 320bd3f9f8)

R2 is deferred by instruction and is not rated.

| id | status | note |
|---|---|---|
| R1 | CLOSED | Text now gives corner 1/(2 pi t_b) = 0.16 Hz (1/(2 pi) = 0.159) and crossover 1.7 Hz, which matches margins.txt (f_c 1.7241 Hz) and the 1.72 Hz in sec:inner_margins. The 4 Hz is gone. Time-versus-frequency comparison removed. |
| R3 | CLOSED | Caption now says same filter chain H, delays set to match. |
| R4 | CLOSED | Sentence after eq:inner_cmd added, with cref to the ground section. |
| R5 | CLOSED | 1/s in text, table (3 rows) and the effective-bandwidth paragraph. |
| R6 | CLOSED | K stated as the effective gain, already halved while ID_OK is 0. Effective-bandwidth paragraph is consistent. |
| R7 | CLOSED | (1+c) weight explained, and condition l=1, c<2 added (default c = 1 or 0.5, so valid). Wording "add the lag that is expected" is vague (see N1). |
| R8 | OPEN (minor) | "per axis and scalar", u and G1 meaning added, H pointer added. B, b, t_b, l, c, Delta_max are still not in the ch02 notation table, and nu bold/non-bold is unchanged. Needs a ch02 edit, outside this chapter. |
| R9 | CLOSED | Reworded, points to the blend. |
| R10 | CLOSED | "a change of 1 takes 0.2 s" (slew 5/s). |
| R11 | CLOSED | Matches the yaml ERPM_TO description (oldest sample older than ERPM_TO, any motor without fresh telemetry). The 20 ms per-sample limit is no longer named, but it is covered by "fresh". |
| R12 | CLOSED | Parameter clause and state-reset note added. |
| R13 | CLOSED | Nine; yaml has 9 INJ entries (listed in the review). |
| R14 | CLOSED | "simulated closed-loop (unit) test"; 80 % of command is supported by results/stage3_s77_tests/README.md (true torque = 0.8 x actuator state). Numbers 0.25 and 1.6e-5 match the README. |
| R15 | CLOSED | 320 and 210 rad/s^2 given; 1757/320 = 5.5 and 1640/210 = 7.8 match "5 to 8". Wording issue in N2. |
| R16 | CLOSED | The chapter shows only the freeze cell (1.72 Hz, 46.9 deg, 15.7 dB, 75.5 ms) and states nothing that depends on the pre-freeze 69 deg. The 4.07 Hz / 69 deg numbers no longer appear. The remaining claim "t_b does not move the margins" rests on pre-freeze PM 68 to 69 at t_b 1.0/0.3/0.1; acceptable, but note it is not shown for the freeze cell. |

## New findings

| id | severity | location | finding | fix |
|---|---|---|---|---|
| N1 | MINOR | lines 99-100 | "these terms add the lag that is expected" is unclear. | "so these terms pre-compensate the lag of u_f." |
| N2 | MINOR | line 186 | "The earlier generic values" refers to a history the reader has not seen, a mild development-trail wording. | "Generic values of 320 and 210 rad/s^2 for roll and pitch (instead) would ..." |

No development-trail file names, code line references or D-/S/Q/A- ids were found in the diff.

Counts: CLOSED 14, OPEN 1 (R8), NEW 2 (both MINOR).

## Orchestrator wording fixes (S262)
- N1 CLOSED: "add the lag that is expected" -> "compensate for this known lag".
- N2 CLOSED: "The earlier generic values" -> "A lower default, for example ..." (no history).
- R8 OPEN (MINOR): symbols B, b, t_b, l, c, Delta_max and bold/plain nu go to the ch02 notation table; carried to the ch01/02 review-and-fix step.
