# F-10 review, commit b34adf0c95 (unit 8)

Verdict: PASS with MINORs (no BLOCKING, no MAJOR)

## Checks
1. Text only: PASS. Both yaml files parsed before/after (python yaml): same parameter set, same
   type/default/min/max/decimal/increment/options/reboot flags/groups/module_name; only description
   short/long and the five new unit entries differ. Short texts unchanged. .msg: only comment text, no field
   or constant line changed (stage_mode comment keeps the [@enum STAGE_MODE] tag). rc.mc_apps and Kconfig:
   comment/help text only. 4040_gz_quad5in: comment only.
2. Project-id grep over the 8 files: no D-/A/G(b)/S/K/Q ids, no indi_flight/indi_project path, no
   owner/gate/freeze/architecture. Remaining hits are physical or plain words: "frozen rotor speed" (short,
   rate yaml:221) physical; "blend_frozen" is a field name (unchanged, fine); "bench excitation" and "ramp"
   are generic.
3. Units: PASS. validation/module_schema.yaml allowed list contains 'rad/s^2', 'rad/s' and '1/s'; stock
   files use them (ekf2/params_gyro_bias.yaml rad/s^2, ekf2/params_drag.yaml 1/s). MC_INDI_LND_SLEW is
   "normalised torque per second", so 1/s is consistent with the stock spelling (normalized_thrust/s also
   exists, but 1/s is acceptable). G2_Y unit rad/s = (rad/s^2) per (1/s), correct.
4. Publisher: IndiRateStatus.msg now says mc_indi_rate_control; McIndiRateControl.cpp/.hpp publishes
   indi_rate_status. Correct. IndiPosStatus/IndiRateFeedforward say mc_indi_pos_control (consumer
   mc_indi_rate_control), consistent with the module split.
5. .msg style: the INDI msgs keep the older "# text (unit)" trailing style; stock mixes it (RateCtrlStatus
   style) with the newer "[unit]" prefix (VehicleThrustSetpoint). Acceptable, not changed by this commit.

## Findings
1. MINOR, mc_indi_rate_control_params.yaml:63-71 (MC_INDI_G2_Y long). Hard to read: "a time that is not the
   motor time constant", design history of the 0.13 s reference value, and "reference 5-inch quadcopter".
   Replace:
   "Yaw angular acceleration from the rotor inertia reaction per unit of normalised torque rate. Together
   with MC_INDI_G1_Y it sets a first order low pass on the yaw torque increment with time constant
   MC_INDI_G2_Y / MC_INDI_G1_Y and unchanged steady state gain. Set to 0 to disable. Too large a value
   reduces the stability margin."
2. MINOR, same file, G1_R/G1_P/G1_Y long (lines ~31, 42, 55): "...in rad/s^2 per unit of normalised
   torque" now repeats the new unit (parameters.instructions: long holds only what unit does not say).
   Replace with "Angular acceleration per unit of normalised torque." (G1_Y: drop "The default is the
   reference 5-inch quadcopter value.", it is a default restatement.)
3. MINOR, MC_INDI_W_MAX long (lines ~17-21): removing "in rad/s" is right (unit exists). Shorten:
   "Rotor speed at which a motor produces its full normalised thrust, assuming thrust grows with the square of
   the rotor speed. Used with ESC rpm telemetry to compute the measured torque (topic
   actuator_torque_measured). Set to 0 to disable, INDI then uses its actuator model."
4. MINOR, MC_INDI_ACT_TC long: "an over-estimate up to twice the true motor time constant keeps the stability
   margins" is tuning rationale; keep only "Time constant of the first order actuator model, also used by the
   rate lead (MC_INDI_LEAD). When unsure, round up."
5. MINOR, MC_INDI_LEAD long: formula-style sentence ("factor of this scale times K_R ... times ACT_TC (at most
   2)") is hard to read. Suggest: "Scales the rate prediction lead that cancels the actuator lag. The lead
   adds up to a factor 2 of this scale times the rate gain times MC_INDI_ACT_TC to the angular acceleration
   feedback gain. Set to 0 to disable. Raises motor command noise."
6. MINOR, MC_INDI_ID_OK long (lines 79-82): re-lists the two options in long (instructions: never re-list
   options; put short detail in option labels). Check whether the entry has options; if so move to labels.
7. MINOR, mc_indi_rate_control_params.yaml MC_INDI_INJ_* (and PINJ_*): the repeated "Bench and system
   identification only." prefix costs flash on every entry and sits oddly with "Set to 0 to disable" wording.
   Acceptable, but consider stating it once on the _AX parameter and "Only used when MC_INDI_INJ_AX is not 0."
   on the others (PINJ_* already does the latter).
8. MINOR, MC_INDI_LND_SLEW long: "The torque is ramped instead of stepped." restates the slew; drop it.
9. MINOR, YAML style: long texts use folded `>-` scalars wrapped at ~120 columns. Folds to one paragraph, so
   the QGC output is correct; stock files mostly use plain one-line scalars, so the wrap is cosmetic only.
10. MINOR, IndiRateFeedforward.msg:6 and IndiPosStatus.msg:33 mention "z only" and "ramp" without
    definition ("INDI stage active (not bypass, landed, ramp, z only)"). Suggest "(not bypass, landed, takeoff
    ramp or altitude only)" matching the stage_mode wording.

## Not verified
Did not run the metadata generator / make px4_sitl module_documentation (no build); schema check is by
reading validation/module_schema.yaml. ID_OK options not inspected. Mixed-style .msg comparison was by
sampling two stock messages.
