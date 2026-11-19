# A-43 probe: why yaw G1_Y fits 163 instead of 205

Files: probe.py (copy of ident_fit_yaw machinery with switches; imports bench/ unmodified).
Commands (cd indi_flight; ulimit -v 4000000; timeout 600):
  python3 results/ident_m3a_s123/a43_probe/probe.py real results/ident_m3a_s123/axyaw/flight.ulg     # window 22.1-76.0
  python3 results/ident_m3a_s123/a43_probe/probe.py real results/ident_m3a_s123/half_ax3/flight.ulg
  python3 results/ident_m3a_s123/a43_probe/probe.py synth
Variants: V0 baseline; V1 y and instruments passed through the same operator as u (sampled at u's 400 Hz stamps, linear
interp to 800 Hz grid); V2 V0 + regressor r = F[C w] (alpha term -D r, D = -beta3, not latency-shifted); V3 = V1 + V2.
Columns: G1, CI, G2, CI, D, J (df, J/df), shift, F_eff (G1/G2/[r]). Physical: G1 205.3, G2 ~27, D ~1.4.

## Real, axyaw
| var | G1 | CI | G2 | CI | D | J | shift | F_eff |
|---|---|---|---|---|---|---|---|---|
| V0 | 163.1 | +-1.2 | 27.53 | +-0.05 | - | 90.6 (df 8, 11.3) | 1 | 3926/91461 |
| V1 | 158.6 | +-1.1 | 27.09 | +-0.05 | - | 72.7 (df 16, 4.5) | 1 | 3932/31148 |
| V2 | 174.8 | +-6.3 | 27.48 | +-0.06 | 0.359 +-0.198 | 91.4 (df 7, 13.1) | 1 | 191/60664/1203 |
| V3 | 211.8 | +-7.1 | 26.90 | +-0.06 | 1.618 +-0.208 | 39.6 (df 15, 2.6) | 1 | 129/19256/636 |

## Real, half_ax3
| V0 | 166.0 | +-1.1 | 27.54 | +-0.04 | - | 96.0 (df 8, 12.0) | 1 | 21371/45071 |
| V1 | 163.4 | +-0.9 | 27.07 | +-0.05 | - | 78.2 (df 16, 4.9) | 1 | 18238/20036 |
| V2 | 153.4 | +-9.3 | 27.60 | +-0.07 | -0.41 +-0.31 | 95.7 (df 7, 13.7) | 1 | 583/24704/259 |
| V3 | 220.1 | +-8.9 | 26.82 | +-0.07 | 1.85 +-0.29 | 54.5 (df 15, 3.6) | 1 | 337/9849/144 |

## V4 synthetic (G1 205.3, G2 27, D 1.4, motor tau 12.5 ms, 400 Hz ZOH P-controller K=0.15 + multisine 0.3-50 Hz, u 400 Hz, gyro 800 Hz)
| S0 (=V0) | 596.9 | +-14.4 | 26.40 | | - | 134.8 (df 8) | 1 | |
| S1 (=V1) | 165.8 | +-0.2 | 27.06 | | - | 133.1 (df 8) | 0 | |
| S2 (=V2) | 2529 | | -21.9 | | 76 | | 10 | (garbage) |
| S3 (=V3) | 204.4 | +-0.0 | 27.04 | | 1.379 | 133.2 (df 7) | 0 | |

## Verdict
1. Cause: omitted rotor-drag yaw damping (-D r). With interpolation matched (S1) the synthetic plant returns 165.8, i.e. the observed ~165, from D = 1.4 alone; adding r (S3) recovers 204.4 and D 1.379 (truth 205.3 / 1.4).
2. Real data agree: V3 (matched interpolation + r) gives G1 211.8 (axyaw) / 220.1 (half_ax3), D 1.62 / 1.85, G2 ~26.9; within ~3-7 % of 205 but CIs (+-7-9) do not cover 205 on half_ax3.
3. Interpolation mismatch alone is NOT the cause: V1 moves G1 only 163 -> 159 (real); on synthetic V0 is unreliable (597), so the interpolation effect is not cleanly characterised.
4. r alone (V2, mismatched interp) is erratic (175 / 153), weak first stage (F_eff G1 130-580); r needs matched interpolation to work.
5. Unverified: synthetic is idealised (linear, no saturation, no sensor lag, S0 blow-up unexplained, J/df 17 so instruments are imperfect); real V3 residual 3-7 % high not explained; half_ax3 D 1.85 vs 1.4.
