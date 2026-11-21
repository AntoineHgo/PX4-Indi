# G7 gtest for kSetpointLeadTc 0.03
Test: IndiRateControlSetpointLeadTest.StaircaseSetpointRippleIsFilteredAt889Hz (src/lib/indi_rate_control/indi_rate_control_test.cpp). 800 Hz, 2 rad/s^2 ramp held every 9 cycles, 800 cycles read after 1 s.
Ripple p-p of rate_sp_dot: 0.652 rad/s^2 (Tc 0.03), 1.867 rad/s^2 (Tc 0.01); mean 2.000 / 2.001. Bound 1.2 (0.6 x mean ramp rate), mean within 10 % of 2.
Break check (gtest_run.sh, docker f4g): Tc 0.01f FAILS (1.867 vs 1.2), Tc 0.03f PASSES. Header restored (no diff). make format run, no further diff.
