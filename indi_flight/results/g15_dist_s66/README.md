# S66 G1.5 disturbance-injector pre-test (quad5in, INDI)

## Command
`bash indi_flight/results/g15_dist_s66/fly.sh` from the repo root. Each line runs
`indi_project/docker/run.sh -n s66d_<sc> -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario <sc> --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 --params $G/indi.params --out $G/<sc>`.
All five scenarios ran in parallel; all returned rc=0 (done.txt). Params: copy of results/g2_step_s64/indi.params.

## Build
Git HEAD of the checkout: 6da5875303 (feat/indi-flight). Binary/sim build inside the container: NOT CHECKED (UNVERIFIED).
Analysis scripts (scratch, not in the results dir): /tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/8efb3381-af56-489c-b87e-ca63a4308ea2/scratchpad/s66_*.py

## Results

| scenario | airframe line OK | wrench peaks as expected | response sign OK | completed |
|---|---|---|---|---|
| torque_steps | yes | yes (0.100/0.100/0.030 N m in 0-2, 4-6, 8-10 s) | roll yes (+3.22 rad/s); pitch NO (-2.99 rad/s); yaw NO (-0.61 rad/s), see frame note | yes (landed) |
| gust_x | yes | yes (Fx peak 0.5954 N at +12.5 s) | NO in brief's NED x sense (x dev <= 0.02 m); yes in the physical wind sense (y, east, +0.29 m at +13 s) | yes |
| payload_add | yes | yes (Fz -1.4945 N, 0-30 s) | thrust rises, but +50 % (0.137 -> 0.205), not +25 % | yes |
| gust_diag | yes | magnitude yes (|Fxy| 0.7098 N at +12.3 s); direction 96.8 deg, not ~120 deg (see notes) | UNVERIFIED (no check run; roll +8 deg, pitch +2 deg peaks) | yes |
| com_shift | yes | yes (Fz -0.8967 N, tx -0.0448 N m, 0-30 s) | mean roll -0.75 deg (sign OK), but a roll excursion of +78.7 / -32.2 deg at +26.1..26.8 s (unexplained) | yes (landed, disarm by landing in px4.log) |

## Details

**Airframe line** (identical in all five, from disturbance.log):
`22:14:25 airframe quad5in: mass 0.6100 kg, inertia (0.001022, 0.001122, 0.001944), CdA 0.012, cop_z 0.02, source .../sim/models/quad5in_base...`
(gust_diag logged 22:14:21). gz_model_info.txt: base_link 0.566 kg plus 0.011 + 0.011 kg link masses, total 0.61 kg.

**CSV.** Columns sim_time_s, px4_time_s, fx, fy, fz, tx, ty, tz. sim_time equals px4_time (CLOCK_OFFSET_S = 0). Onset from run.json disturbance.onset_px4_s:
- torque_steps: onset 60.608 s, rows 9601, span 60.61-72.61 s. Wrench nonzero 0-10 s rel onset; 0 after.
- gust_x: onset 65.951 s, rows 22401, span 65.95-93.95 s. Nonzero 0.02-28.00 s rel; 0 at end.
- payload_add: onset 65.395 s, rows 24001, span 65.40-95.40 s. Nonzero 0-30 s; 0 at end.
- gust_diag: onset 65.565 s, rows 22081, span 65.56-93.17 s. Nonzero 0.02-27.6 s; 0 at end.
- com_shift: onset 65.346 s, rows 24001, span 65.35-95.35 s. Nonzero 0-30 s; 0 at end.

**gust_diag direction.** Base 4 m/s at 45 deg plus gust 8 m/s at 120 deg (DIAG_BASE_DIR / DIAG_GUST_DIR). The vector sum at the gust peak points at about 97 deg, which is what the code produces. The "~120 deg" in the brief is the gust-component direction, so this is consistent with the code and not an injector bug (flag only: the brief's expectation is inaccurate).

**Response details.**
- torque_steps, ulog vehicle_angular_velocity (dt 1.25 ms). p: peak +3.22 rad/s at +0.04 s into window 0-2 s, then reverses to about -1.2 rad/s at 0.2 s and decays (INDI rejects the step; window mean about 0). q: peak -2.99 rad/s at +4.04 s in window 4-6 s, opposite to the +y torque. r: peak -0.61 rad/s at +8.06 s in window 8-10 s, opposite to the +z torque. This is what the injector frame predicts if the wrench is applied in Gazebo ENU/FLU world axes: in PX4 NED/FRD, the sign of pitch (y) and yaw (z) flips relative to ENU/FLU, and roll (x) does not. The gust_x lateral response also confirms the ENU frame (see below). The G1.5 check expected "rate in the sign of the torque", so the literal check fails for q and r; the frame convention needs to be documented or the torque sign mapped to PX4 axes before the G1 use. Frame conversion of gz world to ENU was NOT verified in code.
- gust_x, ulog vehicle_local_position. Local x (NED north) deviation stays within about +-0.02 m (max +0.019 m at 22 s, mean -0.004 m); no clear +x. Local y (NED east): +0.011 at 0, +0.288 at +13 s, +0.129 at +14 s, then back to about 0. The wind is +x in ENU, i.e. east, so the drone moves downwind in the physical sense. Pitch peaks +7.3 deg at +13 s (nose-up). Interpretation: the brief's "x moves +x" uses the wrong frame; the response sign is correct physically.
- payload_add, ulog vehicle_thrust_setpoint (-z). |thrust| 0.1367 pre-onset (-20..0 s) and 0.2047 in 2-28 s, ratio 1.50. Expected ratio about 1.25 (1.49 N on a 5.98 N weight). The extra thrust is about twice the injected force, which is unexplained. Altitude 4.96 m pre, 4.80 m in window. After the profile (31-40 s) thrust returns to 0.135 and altitude drops to 3.93 m (landing/descent; not analysed).
- com_shift, ulog vehicle_attitude. Roll mean -0.75 deg over 0-30 s (sign matches tx < 0). Pitch mean +0.05 deg. But: |roll| > 20 deg in 123 samples between +26.13 and +26.82 s rel onset, max +78.7 deg at +26.29 s, min -32.2 deg; roll goes +15 -> -29 -> -22 -> -13 -> -5 deg within 0.5 s, then -6.6 deg at 29 s. Altitude stayed 4.7-5.1 m, quaternion norm 1.0. No other scenario shows this (gust_x, gust_diag, payload_add, torque_steps max |roll| 0.3-11 deg). px4.log and gz.log show no warning at that time. Cause UNKNOWN; this is UNEXPECTED and needs a look at the flight.ulg (rate and actuator_motors around 26 s) before this profile is used.

**Completion.** All five have run.json and altitude returns to about 0 at the end (final -z: torque_steps 0.01, gust_x 0.00, payload_add -0.01, gust_diag 0.13, com_shift 0.07 m; minimum about -0.12 m). Max altitude 5.0-5.35 m. com_shift px4.log shows "Disarmed by landing"; others not checked (UNVERIFIED).

## Unexpected / open items
1. torque_steps pitch and yaw rate responses have the sign opposite to the injected torque in PX4 FRD axes (consistent with ENU/FLU world axes for the wrench). Frame convention needs documenting or a mapping.
2. gust_x: the drone moves east (NED +y, ENU +x), not north (NED +x). Brief's expected sign is in the wrong frame.
3. payload_add: thrust rise about 50 %, expected 25 %. Unexplained.
4. com_shift: roll excursion up to +78.7 deg / -32.2 deg at +26.1..26.8 s. Unexplained, altitude held.
5. gust_diag peak direction 96.8 deg (vector sum), not ~120 deg (gust component). Consistent with code.
6. Not checked: gust_diag and torque_steps/gust_x/payload_add disarm/landing, binary/sim build hash, and the ulog for gust_diag responses.
