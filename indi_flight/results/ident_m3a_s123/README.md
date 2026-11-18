# M3a ident pretest (S123), quad5in

Command (fly.sh, arg 0 or 1; container s123id<p>, -t 420):
`indi_project/docker/run.sh -n s123id<p> -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/ident_m3a_s123/inj_pos<p>.params --out indi_flight/results/ident_m3a_s123/pos<p>`

Params (inj_pos0/1.params): quad5in G1/G2Y base values, MC_RATE_CTL_TYPE 1, MC_INDI_W_MAX 2700, MC_INDI_POS_EN 0/1,
INJ_AX 1 (roll), INJ_AMP 0.003, TP 10, NP 6, FMIN 1, FMAX 60, INJ_DLY 8 (settle delay param exists). Gains not halved (s39 did not).
Checks: check.py <ulg>.

Precheck (g3_refly_s122/run_000): esc_status, actuator_torque_measured, indi_rate_status, sensor_gyro all median dt 1.25 ms (800 Hz).
esc_status is NOT 100 Hz; the INDI measured path runs on 800 Hz data.

| check | pos0 | pos1 |
|---|---|---|
| injection start (log s) | 20.6, after takeoff | 20.6 |
| injection end (log s) | 78.4 | 78.5 |
| max abs roll (deg) | 7.3 | 7.2 |
| measured_torque_in_use nonzero | 84% of samples | 84% |
| actuator_torque_measured | present, 800 Hz | present, 800 Hz |
| indi_rate_status / esc_status / sensor_gyro dt | 1.25 ms each | 1.25 ms each |
| indi_pos_status | absent (expected) | present, 11.25 ms median dt (~89 Hz) |

Problems: first pos0 flight with INJ_AMP 0.01 gave 25 deg roll (AMP is per component, 18 components: peak torque 0.11,
rms 0.03); kept in pos0_amp0p01_void (void, not for estimation). Re-flown at 0.003 for both. flight.ulg files untracked, do not add.
Unverified: estimator excitation adequacy at AMP 0.003 (SNR) and that 60 s injection (NP 6) satisfies ident_iv.py discard rules.
