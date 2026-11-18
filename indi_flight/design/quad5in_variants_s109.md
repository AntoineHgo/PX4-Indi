# quad5in plant variants (S109)
Plan: build_variant(spec,out,stock_models,model="quad5in") copies quad5in + quad5in_base (sim/models), scales via the same keys
as x500 (ixx/iyy/izz base_link inertia, mass, tau, tau_up, tau_down, imu_rate). 8 timeConstant tags (4 rotors x up/down) in quad5in/model.sdf
(gz multicopter motor model supports Up and Down). mass: base_link 0.566 and the four rotor links 0.011 each scaled (total x factor);
rotor <inertia> (2.5e-5/2.5e-5/5e-5, physical) untouched. Physics step/IMU rate untouched (world default.sdf; imu_rate only if requested).
rpm key rejected on quad5in. Record: run.json meta.model_variant has model, scale, original, new. x500 path unchanged.

## Implemented
bench/model_variant.py: build_variant(..., model="x500"|"quad5in"); bench/run_scenario.py: apply_model_variant passes model, new CLI
`--model-variant mass=1.3,tau=2,tau_up=1.5,ixx=0.7` merged over the scenario's model_variant. x500 path unchanged (checked it builds).
Note: quad5in MotorFailurePlugin kept; ElementTree rewrites the SDF (comments dropped, quotes normalised), values only differ as below.

## Offline diff (mass 1.3, ixx/iyy/izz 0.7, tau 2, tau_up 3 -> up x6, down x2)
base_link mass 0.566 -> 0.7358; rotor masses 0.011 -> 0.0143 (x4); ixx 1.022e-3 -> 7.154e-4, iyy 1.122e-3 -> 7.854e-4, izz 1.944e-3 -> 1.3608e-3;
timeConstantUp 0.033 -> 0.198, timeConstantDown 0.033 -> 0.066 (all 4 rotors); rotor inertia, update rates, physics step unchanged.
## Flight: hover mass x1.3 motors mean 0.1351 -> 0.1749 (x1.295). See results/quad5in_variants_s109/README.md.
Caveat: inertia scale does not include the rotor-mass change (rotor links' own mass scaled with mass, base inertia is not recomputed).
