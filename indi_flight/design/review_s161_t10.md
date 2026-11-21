# S161 review: D-T10-RESET (commit 49568bcaa5), code vs spec

1. resetJerkHistory() state coverage: OK. indi_accel_control.cpp:143-153 clears _time, _a_ff_prev, _j_diff, _lpf_j,
   _t_a_ff_prev[], _a_ff_prev_valid[]: all of updateJerkDifference (:156-192) and nothing else.
   MINOR: _j_diff_f (hpp:264) is not zeroed. It is recomputed at :192 before use at :301 in the same update(), so it is
   harmless, but the state left between the call and the next update() is the old value.
   Frame dependence: OK. No NED vector is stored. _lpf_f/_last_f_b are body frame, _thrust_prev/_b/_u*/_um* are scalars,
   omega_ff is recomputed each cycle (:440-446). Nothing needs rotating at a heading reset.
2. reset(): OK. cpp:109-139 does the same writes in the same order and then calls resetJerkHistory() (:140-153).
   Behaviour is unchanged.
3. McIndiPosControl.cpp: ordering is OK. The detector (:864-867) runs in the main loop before runIndiStage, and the
   pending flag is consumed before the stage update at :279-284.
   MAJOR: the _indi_reset_pending flag is shared with non-estimator events: pos entry (:226), Hold->run (:246-247) and
   resetStageState (:423). The old branch re-seeded the filters for those, and now they only clear the jerk history.
   After Hold, or a pos entry that came from Hold (or any time the stage did not run), _lpf_f, _lpf_u, _lpf_um, the
   delay buffers and _thrust_prev are stale. The Hold->run comment at :245 says the time base did not advance in Hold.
   Bypass cycles still call reset() at :409, so bypass->INDI and the take-off ramp are fine. The :401 clear is unchanged.
   Fix: split the flag, e.g. _indi_reseed_pending (full reset, old code) and _indi_ekf_reset_pending (jerk only).
   Only the detector at :866 should set the jerk-only flag.
   Other raw-sample re-seeds: the bypass reset() at :409 runs only outside INDI. setFilter() at :169 re-seeds from the
   last output, which is fine. No other in-flight raw re-seed found.
4. Unit test ResetJerkHistoryKeepsMeasuredFilters: mostly OK. Re-seeding the force filter or the collective filters
   from the raw sample would make a_f, t_f and t_c differ from the no-reset reference, so it would fail (test :303-331).
   MINOR: the EXPECT_LT(|a_f|, 0.2) line is redundant given the equality checks.
   MAJOR (missing test): nothing checks that resetJerkHistory() clears the jerk history. A test should step a_ff, then
   call resetJerkHistory() in the same cycle, and expect j_diff_f == 0, omega_ff without a spike and out equal to a
   fresh a_ff_prev_valid=false state. It should also run the same step without the reset to show a spike. Deleting the
   body of resetJerkHistory() would pass today.
