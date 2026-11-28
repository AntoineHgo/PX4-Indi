# Proposed captions and symbol lists

Build: `cd indi_flight/report/pdf/diagrams && lualatex -interaction=nonstopmode -output-directory=/tmp/diagbuild preview.tex`.
Each diagram is a bare `tikzpicture`; `\input` it inside `figure` after `diagram_style.tex`. The style file defines
`\indimono{...}` (small monospace) with `\providecommand`, plus the six palette colours with `\providecolor`.

## architecture.tex
Caption: Control chain of a multicopter with the stock PX4 modules (grey) and the two INDI modules (blue, bold outline).
`MC_INDI_POS_EN` and `MC_INDI_EN` select, at start-up, either the stock or the INDI module of a layer; the attitude loop,
the control allocator and the setpoint generation are kept. Both INDI modules use measured signals (orange): rotor speed
from ESC telemetry, accelerometer and gyro.
Symbols: $\dot{\boldsymbol\omega}$ (in the rate INDI box). Uses uORB/module names in small monospace.
Verified: module start logic in `rc.mc_apps` (stock vs INDI selection, `mc_att_control`, `control_allocator`,
`flight_mode_manager`, `mc_hover_thrust_estimator`, `land_detector` kept); topics `indi_rate_feedforward`,
`vehicle_attitude_setpoint`, `trajectory_setpoint`, `unallocated_torque`, `esc_status`; acro handled inside the INDI rate
module (`McIndiRateControl.cpp` manual_control_setpoint branch); offboard publishes `trajectory_setpoint` directly.
Unverified (stock PX4 knowledge, not read in this task):
- The one-line descriptions of the stock boxes ("Position and velocity PID, thrust from hover model", "Rate PID").
- That manual stabilised mode takes `manual_control_setpoint` in `mc_att_control` (stock behaviour), and that
  altitude/position hold and mission/RTL/land/takeoff setpoints all come from `flight_mode_manager`.
- The right-hand bus is one simplified line for all measured inputs: the pos module reads `esc_status`,
  `vehicle_acceleration`; the rate module reads `vehicle_angular_velocity`, `esc_status`. The stock modules' own sensor
  inputs are not drawn. `vehicle_land_detected`, `hover_thrust_estimate` are only mentioned in the footnote line.
- `commander` is listed as kept (it hosts the arming check) but was not checked in `rc.mc_apps`.

## inner_loop.tex
Caption: Rate-loop INDI law for one axis. The rate error gives a desired angular acceleration $\boldsymbol\nu$; the
measured, filtered angular acceleration $\dot{\boldsymbol\omega}_f$ is subtracted, the remainder is inverted through
$G_1$ to an increment $\Delta u$ and added to the filtered actuator state $u_f$. The actuator state blends the measured
rotor speed (high frequencies) with a modelled first-order actuator (low frequencies), and all three paths share the same
delay and filter $H$.
Symbols: $\boldsymbol\omega$, $\boldsymbol\omega_{\mathrm{ref}}$, $\dot{\boldsymbol\omega}_f$,
$\dot{\boldsymbol\omega}_{\mathrm{ref},f}$, $\boldsymbol\nu$, $K$, $c=K\tau_a$, $\tau_a$, $G_1$, $G_2$, $T_s$, $\Delta u$,
$\Delta u_{\mathrm{prev}}$, $u_f$, $u_c$, $u_{\mathrm{meas}}$, $u_{\mathrm{mod}}$, $b$, $u_i=(\Omega_i/\Omega_{\max})^2$,
$\Omega_i$, $H$ (delay + filter chain).
Verified against chapter 1 (sections 2-5) and the notation of the brief: law
$\Delta u=(\nu-(1+c)\dot\omega_f+c\,\dot\omega_{\mathrm{ref}})/G_1$, yaw $(G_1+G_2/T_s)$ backward-Euler term with the previous
increment, blend $b=\mathrm{LP}(u_{\mathrm{mod},f}-u_{\mathrm{meas},f})$, allocated (not commanded) torque feeding the model.
Code only read through the chapter citations, not re-read.
Notes and unverified:
- In the chapter the quantity is a normalised axis torque $t$; the figure writes it $u$ per axis (command $u_c$) per the
  requested notation. The caption or text must say $u\in[-1,1]$ is the per-axis normalised command and that
  $u_i=(\Omega_i/\Omega_{\max})^2$ is mapped to axis torque by the effectiveness matrix (the matrix is not drawn).
- Signs on $u_f$ into the second-from-last sum are "+" (increment form $u_c=u_f+\Delta u$).
- The setpoint low-pass in the lead ($\tau=0.03$ s) and the feed-forward $\omega_{\mathrm{ff}}$ added to $\omega_{\mathrm{ref}}$
  (roll, pitch) are not drawn as separate blocks; the increment limit is only implied by the saturation block.
- Landed handling ($u_f$ held at 0) is a footnote, not a switch.

## outer_loop.tex
Caption: Acceleration-loop INDI of the position controller. The stock position/velocity cascade (integrator off) gives
a reference acceleration $\mathbf{a}_{\mathrm{ref}}$; the measured specific force gives $\mathbf{a}_f$, and the error is
added to the filtered thrust vector $\mathbf{T}_f$ to form $\mathbf{T}_c$. After saturation the thrust vector sets the
attitude setpoint and the collective thrust; a jerk feed-forward drives the rate loop directly. On the ground, in the
take-off ramp and with stale data the force source switches to a modelled force.
Symbols: $\mathbf{p},\mathbf{v},\mathbf{p}_{\mathrm{ref}},\mathbf{v}_{\mathrm{ref}},\mathbf{a}_{\mathrm{ff}},
\mathbf{a}_{\mathrm{ref}},\mathbf{a}_f,\mathbf{f}_b,\mathbf{f}_{b,f},R,\mathbf{g}$, $\mathbf{T}_f,\mathbf{T}_c$, $T_c$,
$\mathbf{q}_d$, $g_t$, $u_i$, $u_{\mathrm{meas},f}$, $u_{\mathrm{mod},f}$, $b$, $\boldsymbol\omega_{\mathrm{ff}}$,
$\mathbf{j}$, $c=\lVert\mathbf{T}_c\rVert$, $\mathbf{x}_b,\mathbf{y}_b,\mathbf{z}_b$, $H$.
Verified against chapter 2 sections 1-5: cascade, $t_c=t_f+(a_c-a_f)$, 10 Hz second-order filter on both paths with delay,
blend and its freeze conditions, saturation order, jerk feed-forward formula, modelled force on ground/ramp/stale,
module outputs.
Notes and unverified:
- Notation: $\mathbf{T}$ is the specific thrust vector (m/s$^2$ units, chapter symbol $t$); $T_c=\lVert\mathbf{T}_c\rVert/g_t$ is the
  collective thrust command after the thrust map ($g_t=g/\text{hover thrust}$). Define this in the text.
- The sum order is drawn as $\mathbf{a}_{\mathrm{ref}}+\mathbf{T}_f$ first, then $-\mathbf{a}_f$ (arithmetically identical to
  $\mathbf{T}_f+(\mathbf{a}_{\mathrm{ref}}-\mathbf{a}_f)$), to avoid crossing lines; the intermediate signal is unnamed.
- $G^{-1}=1$ in specific-thrust units, so no inversion block is drawn.
- The take-off/landing state machine is in ground_logic.tex; here only the "force source" switch is shown. The ramp
  uses the stock ramp for the setpoint (not drawn). The measured-force path delay is shown only by the badge "H".
- "Modelled thrust from $T_c$" is the commanded collective (chapter: `thrust_prev k_cmd`), drawn from the output of the
  thrust-vector block.

## ground_logic.tex
Caption: Operating states of the outer loop. The same INDI law runs from arming to disarming; only the source of the force
and thrust state changes. Ground and ramp use the modelled force, flight uses the measured force and rotor speed, and
touch-down returns to the modelled force and holds the blend.
Symbols: $\boldsymbol\omega_{\mathrm{ff}}$.
Verified against chapter 2 section 5 (ground, ramp, landing; 10 % edge step limit as stated there). The transition labels
are paraphrased ("take-off", "ramp done", "landing", "landed, disarmed"); the actual conditions are take-off state,
`ground_contact` and `landed`/`maybe_landed` flags. The loop back to Ground after landing is simplified (a disarm
resets the state); the state "Touch-down" is not a named state in the code.

## actuator_state.tex
Not produced (the blend is shown in both loop diagrams; the detail is in the inner-loop caption and chapter section 3.4).
