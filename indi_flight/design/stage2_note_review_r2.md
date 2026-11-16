VERDICT: CLOSED

# Review r2 of `stage2_margins_s35.md` section 7 / D-G2-BREAK against r1 and the source (6 tool calls, no build/sim)

(a) Feedback paths from u back to c, with u = c + d written into `vehicle_torque_setpoint.xyz`
1. Publish and store are one value. `McIndiRateControl.cpp:331` stores `Vector3f(vehicle_torque_setpoint.xyz)`, the message
   built at :319-321 and published at :329. One injection into that message before :329 feeds both. It must come after the
   finite-sanitize (:319-321) or inside it, and nothing may inject only into the publish copy.
2. Modelled actuator path: `_prev_torque_setpoint` (:181) -> `t_alloc` (`lib/indi_rate_control/indi_rate_control.cpp:254`)
   -> `_t_act` -> delay -> H -> `t_f_model`. Through u.
3. Unallocated-torque path: :183-185 subtracts `_unallocated_torque` only when its timestamp is newer than
   `_prev_torque_setpoint_time` (set at :332). The allocator computes it as `getControlSetpoint() - allocated`
   (`ControlAllocator.cpp:678-682`), and the setpoint is the received u (:384, :441). So it is a function of u. A stale or
   absent status leaves u_prev, still u. Through u.
4. Measured rotor-speed path: u -> allocator -> motors -> gz rotor -> esc rpm -> `updateMeasuredTorque()` (:338) -> `_torque_measured`
   (:188) -> `setMeasuredTorque` (:193) -> `t_meas` (lib :~330) -> `t_f` blend. Through u (via the plant).
5. Gyro path: u -> plant -> `rates`, `angular_accel` (:242-243) -> `a_f`, `rate_error` -> c. Through u. The outer attitude and
   velocity loops (plant -> `_rates_setpoint` :287-291) also close through u, so L_u includes them at low frequency.
6. c holds no memory of its own output. `_t_f_prev = t_f` (lib :380-384) and the yaw LPFs (lib :~348-360) are fed by t_f, which is
   derived from `torque_allocated_prev`. Output is `t_cmd = clamp(t_fb + dt_cmd)` (lib :~396-399).
Bypasses of u (none in the linear in-flight loop; three off-path items):
   - `_t_cmd_last = t_cmd` (lib :~399) is c-derived internal state. I did not read `faultOutput`, so only fault cycles may use it.
     Keep d small enough to avoid faults and assert `fault == 0` in the run.
   - `landed` zeroes `t_fb` (lib :~372, 7b): c is independent of u on the ground. Do not run M3a near the landed flag.
   - `reset()` and `_prev_torque_setpoint.zero()` while disarmed (:298-301): irrelevant in flight.
   Nonlinear, not a bypass: `t_alloc` clamps u to +-1 (lib :254), and dt/t_cmd clamps (lib :~395-397). Keep |c + d| < 1.
(b) L = -G_cd/G_ud is correct in sign and signals. With y = c (pre) and x = u (post), u = d - L u gives u = d/(1+L) and
   c = -L u, so L = -c/u. It matches r1 l.5-6. The one-period delay is inside L (c_k uses u_{k-1}). c is not logged now:
   `indi_rate_status` carries `torque_increment` and `torque_filtered`, so c = torque_filtered + torque_increment while
   unclamped, or c = u - d with d logged (then L = 1/G_ud - 1, poor conditioning where |L| << 1). Log d and u at cycle rate (S38).
   Single-axis injection measures the per-axis loop with the other axes closed (MIMO cross terms are not isolated).
(c) r1 findings
   - 1 BLOCKING: answered (7.1, D-G2-BREAK). 2 MAJOR D sign: answered (7.2). The D-filter structure (F_w times alpha(20 Hz)) is not restated.
   - 3 MAJOR blend default: answered in words (7.3, 0 = pure measurement). The restated formula and the Tb -> 0 mapping are not written.
   - 4 MAJOR zeta: answered (table withdrawn, r1 values quoted). The Tb 1.0 slow pole (~1 rad/s) is not listed as a risk.
   - 5 answered (7.4). 6 answered for M3a. The M3b check (accel-loop t_f built from post-injection t_c) is NOT answered.
   - 7 (delay check uses the M1 w_c), 8 (model path in l.108) and 9 (motor ceiling at eta 0.5 in the pre-test) are not in section 7. All MINOR.
   - Stale body text still contradicts section 7 (l.56 INDI row "P: M1", l.115/118/120/125-126). The header says section 7 supersedes.
     Risk: the S37 script gets built from the old body. Patch the body in S37.
No BLOCKING or MAJOR r1 finding is left unanswered. Residuals above are MINOR plus the stale text.
