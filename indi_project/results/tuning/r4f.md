# r4f: combined INDI candidate on the tuning set (session 13)

Command: header of `r4f.log` (`bench/params/indi_r4_best.json` = r3 c13 roll/pitch + r4 c10 yaw set, seeds 1-3,
firmware 99634a6b71). 15 flights, 0 failures.

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| PID defaults (r2) | 0.958-0.964 | 1 | 1 | 1 | 1 | 1 |
| INDI r4f | **0.978** | 0.945 | 0.878 | 0.935 | 1.096 | 1.021 |

Motor-rate effort ratio to PID (min-max over seeds): hover 0.99-1.03, step_roll 1.16-1.26, step_pitch 0.63-0.71,
step_yaw 1.11-1.15, rate_step_roll 0.67.

Reading: J is 0.978 vs PID 0.96, a difference inside the hover-term noise (D-hovernoise, ~0.1). Per scenario: INDI
tracks attitude steps better on roll (-12 %) and pitch (-7 %, with ~30 % less motor-rate effort), equals PID on
rate steps (+2 %, with 33 % less effort) and hover, and is worse on yaw steps (+10 %, structural, `r4.md`).
On the tuning set this is a tie under the frozen cost, not a win. Frozen as the INDI tuned candidate (D-freeze).
