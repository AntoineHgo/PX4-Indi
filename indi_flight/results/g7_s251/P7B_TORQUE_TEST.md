# P7B: measured-torque test with hand-computed expected values (review row 11.3d)

Commit 731fc34528 test(mc_indi_rate_control): check measured torque against hand-computed values (only IndiMeasuredTorqueTest.cpp, +155 lines, no firmware change). Docker only, build/px4_sitl_o11. Scripts: ut_torque.sh (build+run target), brk_torque.sh (uses brk.sh), raw logs brk_torque.txt, brk_t1..t6.txt, run_torque_first.log.

## Hand derivation (checked once here)
Geometry: PX4 quad X, FRD. Motor 1 front right (px,py)=(+.2,+.2) km +.1 (CCW); 2 rear left (-.2,-.2) km +.1 (CCW); 3 front left (+.2,-.2) km -.1 (CW); 4 rear right (-.2,+.2) km -.1 (CW). ct=5, axis (0,0,-1).
Per rotor: moment = ct (p x a) - ct km a; p x a = (-py, px, 0) -> roll = -ct py, pitch = ct px, yaw = +ct km.
B rows: roll (-1,+1,+1,-1), pitch (+1,-1,+1,-1), yaw 0.5 (+1,+1,-1,-1), thrust -5 (1,1,1,1). Rows orthogonal, so pinv column = row / |row|^2: roll col = r/4, pitch col = p/4, yaw col = 0.5 (1,1,-1,-1)/1 (|yaw row|^2 = 1), thrust col -0.05.
Scales (ControlAllocationPseudoInverse::updateControlAllocationMatrixScale): roll = pitch = sqrt(|col|^2 / (n/2)) = sqrt((4/16)/2) = 1/(2 sqrt 2) = 0.353553 (n = 4 entries above 1e-3); yaw = max of the yaw column = 0.5. Torque = scale * B u (trim 0).
- hover u=.25 each: roll/pitch/yaw = 0.
- motor 1 at ratio .7 (u .49), others .5 (u .25), du .24: roll = -.24*.353553 = -.0848528, pitch +.0848528, yaw .5*.24*.5 = .06. Other motors by the row signs above.
- pair 1+2 at .7: roll -.24+.24 = 0, pitch 0, yaw .5*(.48)*.5 = .12; pair 3+4: -.12.
- ratios .7,.5,.4,.6 (u .49,.25,.16,.36): roll -.49+.25+.16-.36 = -.44 -> -.155563; pitch .49-.25+.16-.36 = .04 -> .0141421; yaw .5*(.49+.25-.16-.36)=.11 -> .055. Unnormalised: -.44, .04, .11.
Inputs enter as rpm = (omega/omega_max) * omega_max * 60 / 2 pi (the ratio, not the production u), expected values are literals; no allocator, no inversion. Effectiveness fixture still comes from computeEffectivenessMatrix (the geometry path is thereby under test too).

## Tests added (IndiMeasuredTorqueQuadXTest)
HoverGivesNoTorque, OneMotorFasterGivesItsRollPitchYawSigns (4 motors), DiagonalPairFasterIsPureYawWithTheSignOfItsSpin, DifferentSpeedsOnAllMotors, WithoutNormalisationTheTorqueIsThePhysicalOne. Target functional-IndiMeasuredTorque: 23/23 (18 before). astyle: checked=1 reported=0.

## Break table (one edit, revert, rebuilt; brk.sh output is truncated to 20 failure lines so the lists may be a subset)
| test | break | fail seen | revert pass |
|---|---|---|---|
| OneMotor, Diagonal, DifferentSpeeds, Unnormalised | t1 yaw term sign: rotors.cpp `- ct*km*axis` -> `+` | yes, 4 new | 23/23 |
| OneMotor, Diagonal (+ others listed) | t2 drop the square in u (IndiMeasuredTorque.cpp) | yes | 23/23 |
| OneMotor, DifferentSpeeds, Unnormalised | t3 motor index swap `motor ^ 1` | yes, 3 new | 23/23 |
| OneMotor, Diagonal, DifferentSpeeds | t4 motor index reversed `3 - motor` | yes, 3 new | 23/23 |
| OneMotor, Diagonal, DifferentSpeeds | t5 yaw normalisation scale -> 1 (ControlAllocationPseudoInverse.cpp) | yes, 3 new | 23/23 |
| OneMotor, DifferentSpeeds, Unnormalised | t6 roll/pitch sign: `ct*position.cross` -> `-ct*...` | yes, 3 new | 23/23 |
Hover passes under all breaks by construction (all equal). t3 does not fail the diagonal test (the swap maps the pair onto itself), expected. Sources confirmed reverted (git diff -- src shows only the test file).

Unverified: no hardware/SITL run; other indi targets not rerun (only the test file changed).
