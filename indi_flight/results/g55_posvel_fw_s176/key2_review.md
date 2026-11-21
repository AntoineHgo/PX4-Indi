# key2 review, commit 7dd352bae2 vs D-OFFB-POSVEL (read-only; no build)

BLOCKING: none.

MAJOR: none.

MINOR
1. Check 1: x/y gains use MC_INDI_XY_P / MC_INDI_XY_VP at McIndiPosControl.cpp:599-601 (only setPositionGains/setVelocityGains call);
   z (MPC_Z_P, MPC_Z_VEL_P_ACC), I and D unchanged. grep of module and src/lib/indi_accel_control: no remaining MPC_XY_P /
   MPC_XY_VEL_P_ACC reads (no takeoff/land/failsafe/FF/second-instance use). Not a defect.
2. Check 2: names 12/13 chars, unit 1/s, defaults 1.9/3.6 match decision. Ranges 0-10 and 0-20 are sane. yaml:42-63: the `long` text
   repeats `short` ("Position gain of the INDI outer loop"); parameters.instructions says omit repeated content. Keep only
   "Replaces MPC_XY_P when the INDI position module runs." (same for VP). Min 0 allows zero gain; harmless, optional min>0.
3. Check 3 OK: parameters_update() (cpp:482-) runs on parameter_update and calls ModuleParams::updateParams() (cpp:491), then
   re-sets gains at 599-601, so in-flight changes take effect (also called force at cpp:53 and each cycle at cpp:800).
4. Decision says "~15 LOC firmware + a param test"; commit has no test for the new params (no unit test touches MC_INDI_XY_*). Optional.
5. Check 4 OK: `git diff --stat main -- src/modules/mc_pos_control` is empty.
6. Check 5, silent-ignore list. Runtime sets of MPC_XY_P / MPC_XY_VEL_P_ACC aimed at the INDI module: none found in
   indi_flight/bench/params/*.params or ROMFS/.../4040_gz_quad5in (neither sets MPC_XY_P/VEL_P_ACC nor MC_INDI_XY_*). Stale
   references only: indi_flight/bench/g2_outer_model_s164.py:218 and bench/margins_models.py:232 (model the outer loop with
   MPC_XY_P; INDI cells now need 1.9/3.6), design/outer_loop_requirements.md, design/g2_outer_breaks_note.md,
   design/t195_att_outer_key.md, results/g55_gain_probe_s176/fly*.sh and g55_posvel_fw_s176/fly_fwdef.sh (probe scripts that set
   MPC_XY_* now do nothing for INDI; fine for PID). docs/en has no INDI docs naming MC_INDI_*; the MPC_XY_* hits there are generic
   PX4 docs. Airframes in ROMFS using MPC_XY_P are PID-stack airframes, unaffected. Note: a user tuning MPC_XY_P on an INDI
   airframe is now silently ignored; consider documenting in indi_flight docs.

Verdict: key2 agrees (no blocking/major findings).
