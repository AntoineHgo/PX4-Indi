```text
# Second-key check: t53 pretest s25, hover_r1

log: /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/t53_pretest_s25/hover_r1/flight.ulg
sched rows: 6, sim_schedule_applied rows: 6
tolerances (chosen here): position 0.05 m, heading 0.02 rad (wrapped)

## Item 1: anchor instant
vehicle_status first nav_state==14 & armed: 52015000 us
sim_schedule_applied anchor_us (anchor row 3): 52015000 us
rows at/after anchor with anchor_us != measured: none
ITEM 1: AGREE (diff +0 us)

## Item 2: applied vs scheduled time
row  kind                    sched_t_us  expected_us  applied_us   err_us  verdict
0    arm                        30000000     30000000     30000000       +0  AGREE
1    sp_hold                    51000000     51000000     51000000       +0  AGREE
2    mode_offboard              52000000     52000000     52000000       +0  AGREE
3    anchor nav_state=14        52000000     52000000     52015000   +15000  DISAGREE
4    sp_hold                     3000000     55015000     55015000       +0  AGREE
5    sp_hold                     6000000     58015000     58015000       +0  AGREE
nonzero errors: [(3, 15000)]
ITEM 2: DISAGREE

## Item 3: hold setpoints (sp_hold) vs local position at apply time
TS = first trajectory_setpoint at/after apply; LP = last vehicle_local_position at/before apply
row  apply_us    TS_dt_us  TS x/y/z/yaw                       LP x/y/z/heading                   d_x     d_y     d_z    d_psi   sp-TS max  verdict
1      51000000         0  +0.032/+0.038/-4.956/+1.587  +0.047/+0.022/-4.968/+1.587  -0.0146 +0.0164 +0.0119 -0.0001  0.0166  AGREE
4      55015000         0  +0.059/+0.051/-4.965/+1.587  +0.059/+0.051/-4.965/+1.587  +0.0000 +0.0000 +0.0000 +0.0000  0.0000  AGREE
5      58015000         0  +0.060/+0.027/-4.969/+1.587  +0.060/+0.027/-4.969/+1.587  +0.0000 +0.0000 +0.0000 +0.0000  0.0000  AGREE
ITEM 3: AGREE
```

## Orchestrator reading (S25)
- Item 2: the anchor row's time field (52.000 s) is only its activation time; by design it applies at the observed
  transition (52.015 s, = item 1). Not a defect. Rows after it: 0 us error. AGREE on the intended behaviour.
- Item 3 row 1 (51 s, before offboard): in Hold mode the flight task also publishes trajectory_setpoint, so "the
  next trajectory_setpoint" is likely not the player's. Closing check (S26): compare the `sp` field of
  sim_schedule_applied with vehicle_local_position at apply time instead. Rows 4-5 (in offboard) match exactly.
