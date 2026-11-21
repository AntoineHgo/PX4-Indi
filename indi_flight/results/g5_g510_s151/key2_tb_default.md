# key2: MC_INDI_POS_TB default 1.0 -> 0.3 (S151)

## Q1 consumers
Single consumer chain: McIndiPosControl.cpp:551 setBlendTimeConstant(_param_indi_tb.get()) -> indi_accel_control.cpp:102-110.
Setter: tb > FLT_EPSILON accepted, else _tb = 0 and _b = 0 (TB=0 disable path unchanged, 0.3 does not touch it).
Only use in the loop: indi_accel_control.cpp:347-350, alpha = dt/(tb+dt), no division by tb alone, always in (0,1).
At dt = 2.5 ms (400 Hz) alpha ~ 0.0083, at 4 ms 0.013: stable, no minimum needed. dt is already bounded by kMinDt/kMaxDt (:261).
Freeze paths (:343-347: hold flag, !u_valid, coll_clamped, u_at_limit, alloc_saturated) skip the update; they do not
depend on tb, so unaffected. reset() (:113-127) does not read tb; arm/disarm clearing of b is in the module. Clamp kMaxBlend 0.5 (hpp:87).
At 0.3 s the blend reaches the clamp faster: windup is guarded by the freeze flags, same as before.
Line :335 and :353 use (_tb > 0) only as a flag. No findings.

## Q2 tests assuming 1.0
IndiAccelControlTest.cpp sets tb explicitly (startBlend(tb), 0.2f at :1156/:1197/:1239/:1242); no test reads the param default
or hard-codes 1.0 s for the blend. Run lengths ("10 tb", :822/:836, :931) are relative to the tb passed. Nothing inconsistent.
No unit test of the module-level param default exists.

## Q3 yaml
mc_indi_pos_control_params.yaml:31-41: min 0, max 5, decimal 1, increment 0.1, default 0.3. Valid (0.3 on the 0.1 grid, in range).

## Q4 other params files
bench/params: only quad5in_indi_defaults.params (updated, :41) and quad5in_indi_g1.params (no TB line, G1 only). Clean.

## Findings
BLOCKING: none.
MAJOR: none.
MINOR-1: stale documentation of the default at 1.0: indi_flight/design/key_k127_defaults.md:31 ("default 1.0") and
  design/defaults_audit_s138.md:30 (FW default 1.0). Historical audit records, but should get a superseded-by-D-GAP-G510 note.
MINOR-2: DECISIONS D-GAP-G510 S151 outcome covers z accel-break PM only (62.7/67.3 deg). The xy outer margin was 49.7 deg at TB 1.0
  (defaults_audit_s138.md:30, 5 deg over the 45 gate) and xy was not re-measured at 0.3. Blend acts on the collective, so xy
  coupling is second order (thrust vector tilt scales with u_f), but the xy floor is not evidenced. Suggest one xy cell or a stated argument.
MINOR-3: D-GAP-G510 line 2 still says "kMaxBlend 0.3" as evidence (historical, correct), and the general D-GAP entry (~:470) still
  proposes 1.0 s with the 0.046 vs 0.107 m post-event transient trade-off; the larger post-event transient at 0.3 s is not mentioned in the S151 outcome.

Verdict: ACCEPT, code is numerically safe and consistent; only doc/xy-evidence nits.
