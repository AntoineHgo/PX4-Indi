# Speed factor 1 vs 4, PID default, seeds 1-3 (mean / min..max)

| scenario | metric | speed 1 | speed 4 |
|---|---|---|---|
| step_roll | rate_tracking.roll_rms_rad_s | 0.08662 (0.08418..0.0884) n=3 | 0.08559 (0.08478..0.08653) n=3 |
| step_roll | attitude_tracking.roll_rms_deg | 3.295 (3.205..3.37) n=3 | 3.379 (3.337..3.423) n=3 |
| step_roll | step_summary.rise_10_90_s_mean | 0.4106 (0.4033..0.4144) n=3 | 0.4105 (0.4034..0.4141) n=3 |
| step_roll | step_summary.overshoot_pct_mean | 0.1393 (0.128..0.1568) n=3 | 0.1366 (0.1289..0.1517) n=3 |
| rate_step_roll | rate_tracking.roll_rms_rad_s | 0.3475 (0.3401..0.3522) n=3 | 0.3453 (0.3403..0.355) n=3 |
| rate_step_roll | effort.motor_rate_rms_per_s | 3.261 (3.205..3.29) n=3 | 3.292 (3.291..3.293) n=3 |
| hover | position.rms_3d_m | 0.02684 (0.02097..0.03299) n=3 | 0.06399 (0.03804..0.104) n=3 |
| hover | rate_tracking.roll_rms_rad_s | 0.0009809 (0.0009368..0.001008) n=3 | 0.0009469 (0.0009295..0.0009557) n=3 |
| hover | effort.motor_rate_rms_per_s | 0.03661 (0.03639..0.0368) n=3 | 0.03709 (0.03698..0.03718) n=3 |
