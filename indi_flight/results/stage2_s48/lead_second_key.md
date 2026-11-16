# Second key: INDI roll rate loop with rate-prediction lead (continuous time)

## Derivation
1. Plant: w = A u / s, so a_f = H s w = H A u. Attitude att = w/s.
2. Rate command: nu = K(rate_sp - F w) - K tau_c a_f, rate_sp = -P w/s (att_sp = 0 for the loop).
3. Law with u broken: u_out = H Am e^{-sT} u + nu - a_f.
4. Returned signal R/u = H Am e^{-sT} - (1 + K tau_c) H A - K (F + P/s) A/s.
5. L = -R/u = (1 + K tau_c) H A + K (F + P/s) A/s - H Am e^{-sT}.
   With matched model, the H A and H Am e^{-sT} terms cancel to H A (1 - e^{-sT/...}) ~ H A s T (only the extra sample delay remains); the loop is then K(F+P/s)A/s plus a tau_c term.
6. tau_c = tau: (1+K tau_c) H A + K F A/s with A ~ 1/(1+s tau) gives K F (1+s tau_c)... see sentence below.
7. Grid 0.2-399 Hz log, 400k points. PM at every |L|=1 crossing, GM at every Im L=0, Re L<0 crossing (low <0.5 Hz crossings flagged separately; none appeared).

Physical reason: the lead term -K tau_c a_f feeds back K tau_c * (s w) = K tau_c * A u, which multiplied against the 1/s rate integrator gives K F (1 + s tau_c) A / s; with tau_c = tau this numerator zero cancels the actuator pole 1/(1+s tau), so the rate loop looks like a pure integrator K F e^{-sT/2}/s plus delays.
Cost: a_f is a differentiated (noisy) gyro signal, and it is now multiplied by an extra gain K tau_c (20 x 0.033 = 0.66 at K20, 2.0 at K60), raising the high-frequency noise gain by the same factor, only limited by the 40 Hz / 20 Hz filters.

## Script
See lead_second_key.py (same directory).

## Results (second key, continuous time) vs first key (discrete z-domain)
| case | PM all (deg @Hz) | GM all (dB @Hz) | DM ms (main) | key1 PM/fc/GM/DM | verdict |
|--|--|--|--|--|--|
| K20 tc0 P8 | 29.1@2.99 | 21.0@11.33, 27.1@15.49, 35.3@30.26 | 27.1 | 28.6/2.97/14.2/26.8 | DISAGREE (mine 29.1/2.99/21.0/27.1) |
| K20 tc0 P3 | 44.1@2.79 | 35.6@31.08 | 44.0 | 43.8/2.81/15.7/43.3 | DISAGREE (mine 44.1/2.79/35.6/44.0) |
| K20 tc0 P0 | 54.6@2.72 | 35.7@31.52 | 55.7 | 53.7/2.78/16.5/53.6 | DISAGREE (mine 54.6/2.72/35.7/55.7) |
| K20 tc.033 P8 | 61.3@3.06 | 19.2@22.74 | 55.8 | 60.8/3.02/16.3/55.8 | DISAGREE (mine 61.3/3.06/19.2/55.8) |
| K40 tc0 P8 | 20.5@4.76 | 11.0@9.63 | 11.9 | 19.8/4.74/8.7/11.6 | DISAGREE (mine 20.5/4.76/11.0/11.9) |
| K40 tc.033 P8 | 58.3@6.62 | 12.2@21.09 | 24.5 | 56.0/6.65/10.7/23.4 | AGREE (mine 58.3/6.62/12.2/24.5) |
| K60 tc.033 P8 | 44.1@9.94 | 8.3@20.60 | 12.3 | 41.1/9.91/7.4/11.5 | AGREE (mine 44.1/9.94/8.3/12.3) |

## Verdict
PM and f_c/DM AGREE within 1-3 deg and 1.1 ms for all 7 rows (second key is 0.5-3 deg higher, consistent with half-sample ZOH being slightly optimistic). The GM column DISAGREES strongly (>1.5 dB) on 5 of 7 rows (second key much larger: 21 vs 14.2, 35.6 vs 15.7, 35.7 vs 16.5, 19.2 vs 16.3, 11.0 vs 8.7); only K40 tc.033 and K60 tc.033 agree on GM. The mismatch is not discretisation-size: with tau_c = 0 and P = 0, |L| at the 31 Hz phase crossing is ~0.017 analytically (K F A/s plus the H A sT residual), i.e. ~35 dB, which the first key's 16.5 dB cannot reproduce. The first key's GM is probably taken at a different crossing (e.g. a high-frequency or discrete-derivative artefact, or a different definition of GM), or its model has a residual term that the matched-model cancellation removes here. Unresolved: needs the first key's GM crossing frequency.
