# Key review: quad5in plant variants (bd612779a1), S109

Offline check: build_variant({mass1.3, ixx.7, iyy1.2, izz.9, tau2, tau_up1, tau_down3}, model=quad5in) vs stock sim/models.
Numeric diff (element-wise, XML-parsed): only base mass .566->.7358, ixx 1.022e-3->7.154e-4, iyy 1.122e-3->1.3464e-3, izz 1.944e-3->1.7496e-3,
4 rotor masses .011->.0143, 4x timeConstantUp .033->.066, 4x timeConstantDown .033->.198 (=.033*2*3). Nothing else changed: rotor inertia
(2.5e-5/5e-5), rotorVelocitySlowdownSim=10, IMU update_rate 50/100/800/30 and the 0 on quad5in model.sdf:81 are identical. No max_step_size in
quad5in SDFs (world, not touched). Record holds original+new for every value (rotor_mass, timeConstantUp/Down lists included).

BLOCKING: none.
MAJOR: sampled run record -> runner path is not implemented in the repo. g3_sample.py:240 emits hooks["model_variant"] (keys tau,tau_up,
  tau_down,mass,ixx,iyy,izz = exactly ALLOWED, so no key mismatch), but nothing outside the sampler and its test reads record["hooks"];
  run_scenario.py only takes --model-variant K=V,... (:610, :723-724). The 300-run driver must flatten hooks to that string. Until a
  driver exists and is tested, a flattening bug (e.g. tau_up dropped) is silent.
MINOR: --model-variant parse (run_scenario.py:724) is bare float(): no validation of range (mass=0, negative, nan accepted), a malformed
  item gives a raw ValueError/IndexError traceback; unknown keys are caught later in build_variant (OK). Reuse of the key with scenario variant
  silently overrides (documented in help). rpm=1 on quad5in correctly raises.
MINOR: only mass is flown (commit message); tau/asym/inertia on quad5in verified offline only. Mass also scales the 4 rotor link masses
  (beyond spec wording, consistent with x500 note and recorded); base inertia is NOT rescaled with mass (independent ixx/iyy/izz, per spec).
OK: no other mass/inertia/tau copy in quad5in SDFs (motor plugins carry only timeConstant; one inertial per link); x500 path unchanged
  (default model="x500", record only gains a "model" key).
