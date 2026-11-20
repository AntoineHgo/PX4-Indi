# S134 F-7 smoke flight: auto_tour, INDI position stage from arming (G5.4 take-off row probe)

Probe, not gate evidence. quad5in, seed 1, params `indi_flight/results/auto_smoke_s132/params.params` (MC_RATE_CTL_TYPE 1, MC_INDI_POS_EN 1). Firmware: built px4_sitl, not rebuilt. Raw `flight.ulg`, px4.log untracked.

    timeout 600 indi_project/docker/run.sh -n s134f7tour -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario auto_tour --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/auto_smoke_s132/params.params --out indi_flight/results/f7_smoke_s134/auto_tour
    python3 indi_flight/bench/auto_smoke_check.py indi_flight/results/f7_smoke_s134/auto_tour --json .../check.json > .../check.txt

exit ok, no LOC or failsafe. s132 README has no auto_tour (auto_land10 only); its seed-1 values are the comparison.
- Take-off edge (rampup->flight, 34.40 s): thrust step 0.0064 (checker, 50 ms means) = 4.7 % of hover 0.137; 0.1 s means 0.0060 (4.4 %).
- Truth altitude dip within 1 s after edge: 0.000 m (pre-edge 0.421 m max, post-edge min 0.422 m).
- Max |collective change| over consecutive 0.1 s means, ramp from rampup+0.5 s (31.9 s) to edge: 0.0102 (at 32.10 s).
- Ground collective before rampup (pre-arm, 26.4-31.4 s): mean 0.0145, range 0.001-0.050.
- stage_mode: 2 from 30.16 s (ground/ramp), 1 at 34.40 s (edge) through flight, back to 2 at 92.05 s (landing). s132 had 1 in every sample.
- Mission xy RMS 0.490 m (max 0.785); s131 reference 0.491 m.
- Landing: mean vz 0.707 m/s (MPC_LAND_SPEED 0.70; s132 0.704). Contact 92.04 s, landed 92.72 s, disarm 94.73 s (contact->disarm 2.69 s; s132 2.68 s).
