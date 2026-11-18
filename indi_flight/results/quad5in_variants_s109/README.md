# quad5in plant variants, flight check (S109)
Command (nom: no flag; m13: `--model-variant mass=1.3`):
`indi_project/docker/run.sh -n q5v_m13 -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --rate-hz 800 --model-variant mass=1.3 --out indi_flight/results/quad5in_variants_s109/m13`
Result (hover window = flight end -20 s .. -5 s, mean of 4 actuator_motors commands, alt ~4.9 m both):
nominal 0.1351, mass x1.3 0.1749, ratio 1.295 (expected ~1.3 for hover thrust; the motor command is nearly linear in thrust here
because the thrust curve is near-linear at this level). run.json model_variant holds model, scale, original, new. Nominal run.json has model_variant null.
