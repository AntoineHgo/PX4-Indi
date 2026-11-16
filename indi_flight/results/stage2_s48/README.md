# S48: why the INDI roll M3a phase margin is low (22 deg), and what removes it

Scripts: `bench/att_loop_model_s48.py` (-> `att_loop_model.md`), `bench/sweep_matched_tau_s48.py` (-> `sweep_matched_tau.md`),
`bench/lead_model_s48.py` (-> `lead_model.md`). All are discrete models built on `margins_models.L_indi` (keyed S38).
Second key: `lead_second_key.md` (T101). Flight check of the model's predictions: `m3a_check/`.

## 1. The model with the attitude P loop reproduces the S47 measurement
S47 measured (model-only path, K_R 20, ACT_TC 0.02, plant tau 0.033, MC_ROLL_P 8, 800 Hz, AMP 0.001):
PM 22.3 deg @ 3.48 Hz, GM 4.1 dB, DM 17.9 ms. Model with rate_sp = P_att (att_sp - att) added: PM 23.6 deg @ 3.48 Hz,
GM 4.7 dB, DM 18.8 ms. Per bin above 2.5 Hz the model is within 1.5 dB and 4 deg. Below 2 Hz the measured phase is
up to 14 deg more negative (1 Hz: -169 vs -155): a slower loop around the attitude loop (velocity/position, or attitude
estimate lag) not in the model; it does not move the crossover (A-26).
So A-21's 17 deg gap was the missing attitude loop (S41 hypothesis) plus the G1 error (A-23): explained.

## 2. What limits the margin
With the actuator model matched (ACT_TC = plant tau), the INDI loop at the torque break is close to
L ~ K A(s) (1 + P_att/s) / s, A = motor lag. The phase at crossover is -90 - atan(w_c tau) - atan(P_att/w_c) - delays.
Filters (gyro LPF2p 40 Hz, D-term alpha 20/30/50 Hz) change PM by < 0.2 deg (they cancel in matched INDI).
- K_R 20: P 0/3/5/8 -> PM 53.7/43.8/37.4/28.6 deg, GM 14-16 dB. Raising K_R makes it WORSE (K30 P8 24 deg): the motor
  lag, not the rate gain, is the limit. G2 (PM >= 45) at this break needs P_att <= ~2.5 with K_R 20: an attitude loop of
  ~0.4 Hz, unusable.
- The ACT_TC default 0.02 vs plant 0.033 costs 5 deg PM and 9.5 dB GM (K20 P8: 23.6/4.7 vs 28.6/14.2): ACT_TC is a
  physical parameter (identified, lesson 8); its default was never identified for this airframe.
- PID reference (airframe gains, G1 1757): PM 42.9 deg @ 6.6 Hz with P 8. PID's D on measured acceleration is a lead that
  cancels part of the motor lag; INDI's rate law has no lead.

## 3. Candidate remedy (stage 3 design, not tuned here): rate-prediction lead
nu = K (rate_sp - F w) - K tau_c a_f, tau_c = identified actuator tau. Then L ~ K/s: the actuator pole is cancelled by the
rate prediction w + tau w'. Model (800 Hz, matched ACT_TC, P_att 8): K20 -> PM 60.8 / GM 16.3 dB / DM 56 ms; K40 -> 56.0 /
10.7 / 23 ms; K60 -> 41.1 / 7.4. At 400 and 250 Hz, K40: 53.0/9.6 and 49.6/8.6. Cost: the angular-acceleration feedback
gain becomes (1 + K tau_c) (2.3 at K40), which raises motor-command noise (G4). Equivalent to scaling the a_f term of
the increment; one parameter, tied to the identified ACT_TC (decision 4: bandwidths that transfer).
