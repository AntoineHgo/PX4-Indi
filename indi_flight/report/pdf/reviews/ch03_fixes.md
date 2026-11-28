# Fixes for chapters/03_inner_loop.tex

| id | result | change | source checked |
|---|---|---|---|
| R1 | fixed | Dropped "about 4 Hz". Now: blend corner 1/(2 pi t_b) = 0.16 Hz, far below the measured rate crossover 1.7 Hz (cross-ref to the margins section). | results/freeze10_s193/g2s/roll800_fwdef_s2/margins.txt (f_c 1.724 Hz, PM 46.9, GM 15.7, DM 75.5 ms); t_b default 1.0 in mc_indi_rate_control_params.yaml; the 4.07 Hz is from pre-freeze cells (report/g2_margins.md 2.1) |
| R2 | carried | Not touched (limits chapter 07). Forward references to ch:limits kept. | - |
| R3 | fixed | Caption: "same filter chain H; the delays are set so that they match". Also updated in diagrams/CAPTIONS.md. | review evidence |
| R4 | fixed | Added sentence after the command equation: u_f is the feedback torque after ground handling. | review evidence |
| R5 | fixed | K unit now 1/s everywhere (text, table, effective-bandwidth paragraph). | yaml (rad/s per rad/s) |
| R6 | fixed | Text says K is the effective gain, already halved while ID_OK is 0. | review evidence |
| R7 | fixed | One sentence explains the (1+c) weight and the c term as lag compensation; condition l=1, c<2 added. | review evidence |
| R8 | fixed | Added "per axis and scalar", u = normalised torque of one axis, G1 = diagonal entry; H is now introduced with a pointer at first use. ch02 notation table not edited (other chapter). | - |
| R9 | fixed | Now: switch for all axes together because model and measurement differ in lag; blend follows. | review evidence |
| R10 | fixed | "a change of 1 takes 0.2 s". | yaml LND_SLEW 5/s |
| R11 | fixed | Arming condition now: any rotor without a fresh, plausible, non-stuck sample, or oldest sample older than MC_INDI_ERPM_TO. | review evidence |
| R12 | fixed | Added non-finite/out-of-range parameter; added note that a non-finite increment resets states at once. | review evidence |
| R13 | fixed | "Nine more parameters". | yaml: 9 MC_INDI_INJ_* entries counted |
| R14 | fixed | "simulated closed-loop (unit) test", "one motor that delivered 80 % of its command". | results/stage3_s77_tests/README.md (true torque = 0.8 x actuator state) |
| R15 | fixed | Gave the earlier generic values: 320 and 210 rad/s^2 (roll, pitch); 1757/320 = 5.5, 1640/210 = 7.8. | report/01_inner_loop_design.md section 7 |
| R16 | partly | ch05 does not mention the rate cell or crossover, so no mismatch found. The PM gap pre-freeze 69 vs 46.9 is left unexplained in the text, as the source does not explain it. | report/01_inner_loop_design.md section 8 |
