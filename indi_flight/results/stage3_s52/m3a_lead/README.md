# S52: roll M3a margins with the rate lead (MC_INDI_LEAD 1)

Binary: 6e82b66300 (lead commit; built S52). Model-only path, quad5in, hover_long, speed 4, M3a torque-setpoint
break on roll, AMP 0.001, 18 bins 1-50 Hz. Params `lead1.params` = S48 `tc33_p8.params` (derived G1/G2, ACT_TC 0.033
= plant, MC_ROLL_P 8 default) + MC_INDI_LEAD 1. Flown by `fly.sh`, post by `post.sh` (S48 scripts, paths changed).

| run | lead | ACT_TC | PM deg | f_c Hz | GM dB | DM ms | Ms dB | pre-injection gate (air+4 s, 15 s) |
|---|---|---|---|---|---|---|---|---|
| S48 tc33_p8 s1 (reference) | 0 | 0.033 | 25.9 | 2.92 | 10.7 | 24.6 | 7.5 | - |
| lead1_s1 | 1 | 0.033 | 59.1 | 2.87 | 13.9 | 57.2 | 2.8 | PASS (RMS 0.0037/0.0027/0.0003, pin 0) |
| lead1_s2 | 1 | 0.033 | 59.1 | 2.89 | 14.3 | 56.9 | 2.7 | PASS (RMS 0.0034/0.0038/0.0004, pin 0) |
| lead1tc20_s1 | 1 | 0.020 | 42.0 | 3.33 | 7.9 | 35.0 | 6.1 | PASS (RMS 0.0026/0.0046/0.0005, pin 0) |
| lead1tc20_s2 | 1 | 0.020 | 42.0 | 3.36 | 7.8 | 34.7 | 6.1 | PASS (RMS 0.0033/0.0028/0.0005, pin 0) |

- PM +33 deg, GM +3.4 dB, delay margin x2.3; the two seeds agree within 0.4 dB / 0.1 deg. Model prediction (S48/S49,
  K 20, 800 Hz, 2.5 ms unmodelled delay): PM 56-61, GM 11-16 dB. Unit-test closed loop (T107): PM 65.5, GM 15.7.
- Against G2 (GM >= 6 dB, PM >= 45 deg): roll torque break at 800 Hz meets both on this configuration. Not a gate
  result: one break point, one rate, ACT_TC set to the plant value by hand (identification is stage 4), not --gate.
- The default `_gate.md` (window air+15 s, 30 s) FAILS on roll RMS 0.20 because it overlaps the injection that starts
  at air+20 s (same in S48: 0.247). The `_gate_preinj.md` window ends before the injection; that is the valid check.
- Yaw lead is on (c_Y = K_Y x 0.033): yaw RMS <= 0.0004 rad/s, no recurrence of the A-25 41 Hz limit cycle. Yaw margins
  are not measured (review F3 stays open).
- ACT_TC 0.02 (firmware default, x0.6 of the plant; `fly_tc20.sh`): PM 42.0, GM 7.8-7.9 dB on both seeds, i.e. BELOW the
  G2 PM 45. Unit test predicted 44.9/9.5 (flight 3 deg / 1.6 dB lower, as the unmodelled ~2.5 ms delay of S49).
  Under-estimating tau_c is the weak side (unit test x1.4: PM 83, GM 13). Consequence for defaults (S53 decision): with
  the lead, an over-estimated ACT_TC is safe and an under-estimated one is not, so the default (and the stage-4
  identification) must err high; the 0.02 default does not meet G2 on the reference airframe even with the lead.
