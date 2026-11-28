# Fixes for chapter 4 review (chapters/04_outer_loop.tex)

| Id | Status | What changed / why |
|----|--------|--------------------|
| R1 | FIXED | Reset text now: stage reset keeps the blend, re-seeds delay line and filter from the measured rotor state if valid, else commanded collective minus blend; only arm/disarm clear the blend (checked: resetBlend only at arm edges, "b is held, never reset" in reset()). |
| R2 | FIXED | W_MAX must be set, default 0 blocks arming (checked: rate module "Arming denied: set MC_INDI_W_MAX"). Fallback to commanded collective is for offline motor or stale ESC data. Text, guards list and table row rewritten. |
| R3 | FIXED | Freshness paragraph is now a per-signal list of what a stale value does; table row "Measured" says attitude and acceleration fresh. |
| R4 | FIXED in chapter | Scalar renamed T_col; vector keeps T_c. NOTE: diagrams/outer_loop.tex still labels the scalar T_c (lines 11, 36, 51, 53); it is outside my allowed files and needs T_c -> T_col there. |
| R5 | FIXED | Magnitude of the thrust vector is now tau (was c), clashing with ch03 removed. |
| R6 | FIXED | Blend uses \ts for the period; extrapolation age is delta; scalar u_meas,f explained as mean of four rotors. |
| R7 | FIXED | K_p, K_v stated diagonal, horizontal entries shown, vertical stock; "stock derivative term" dropped. |
| R8 | FIXED in chapter | "4 to 5 % ... always below a limit of 10 %" (source: G5.9d). diagrams/ground_logic.tex caption still says "at most 10 %": needs the same edit (outside my files). |
| R9 | FIXED | Design reason given (0.25 vs 0.04 m/s^2 vibration, about 2 deg, marked as simulation); history removed. |
| R10 | FIXED | Stage rate about 89 Hz in the reference simulation added; line marked as simulated. |
| R11 | FIXED | "for example about 267 Hz in the reference simulation". |
| R12 | FIXED | Interval above 0.2 s holds; shorter clamped to 2 ms. |
| R13 | FIXED | (a) 100 m/s^2 also in flight with ground contact; (b) only vertical feed-forward, when a vertical velocity setpoint is given; (c) altitude-derivative blend described for descent or climb at commanded vertical speed without altitude control. |
| R14 | FIXED | "In flight, while the estimate is valid", floor 0.05 stated. |
| R15 | FIXED | Rate feed-forward zero below 1 m/s^2 added (text and constants); four-rotor statement added. |
| R16 | FIXED | Both negative-history sentences replaced by the positive statement. |
| R17 | FIXED | Blend argument with rho and a_f = a_ref - (1-rho) T_c added, plus the contrast with a wrong g_t. |

Unverified by me beyond the review: the 4 to 5 % figure was taken from the review's citation of the validation chapter. Source line numbers were not re-read except the reset, resetBlend, W_MAX arming and kMinThrustForFf checks.
