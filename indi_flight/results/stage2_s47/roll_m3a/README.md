# S47 roll M3a margins with derived G1 (quad5in, 800 Hz, hover_long, raw logs untracked)

Only flight 1 flown: the pre-test gate failed, so flights 2-4 were not flown (brief: stop and report).

| flight | params | seed | run | checks.py | pretest_gate | PM | GM | min 1/abs(L) at arg L within 10 deg of -180 | DM | bins |
|---|---|---|---|---|---|---|---|---|---|---|
| model_s1 | inj_model_g1 | 1 | rc 0 | pass (rc 0) | FAIL (rc 1) | 32.4 deg @ 3.81 Hz | 6.69 dB @ 8.61 Hz | not computed | 23.6 ms | 18/18 |
| model_s1_a010, model_s2, measured_s1 | | | not flown | | | | | | | |

Margins stdout: `model_s1_margins.txt` (Ms 2.15 = 6.7 dB; arg L is -142 to -148 deg between 2.5 and 4 Hz, so the bins are coherent
near crossover; the |L| curve crosses 0 dB between 3.2 and 4.0 Hz). Checks: `model_s1_checks.txt` (fault 0, landed 0, u=c+d 3.7e-9,
generator 2.95e-9 at t0, height 5.04 m at t0, window 52.02-82.02 s). Gate: `model_s1_gate.md`.

## Gate result (flight 1)
Window 47.02-77.02 s (first airborne + 15 s, 30 s). It OVERLAPS the injection (t0 = 52.02 s), so 25 of its 30 s are injected
and its rate RMS and pin figures mix the injection response with the hover. Numbers: rate RMS x/y/z 1.148 / 0.145 / 0.226 rad/s
(limit 0.02), motor pin 0.261 (limit 0.01), torque achieved 0.755 (limit 0.90).

## Diagnosis (brief, `pre_rms.py`, `diag.py`, spectra of vehicle_angular_velocity)
- Before the injection (44-51 s, so roll was already clean there): roll-rate std 0.016 rad/s (peak 6.4 Hz), pitch 0.015,
  but yaw std 0.18-0.31 rad/s, dominant line at 42.7 Hz in every segment (36-44, 44-51, 60-70 s), and motor pin 0.37 at 35-45 s,
  0.13 at 45-50 s. So the vehicle is NOT in a roll limit cycle at rest, but there is a yaw oscillation near 43 Hz with the
  yaw G1 1757/1640/205 set (MC_INDI_G1_Y 205), which pins motors.
- During the injection roll rate std is 1.0-1.2 rad/s (max roll 21 deg) with energy at 2.5-4 Hz, i.e. at crossover. Whether
  that is just the closed-loop response to d at 4 Hz with Ms 2.15 or a nonlinear (motor pin / yaw coupled) effect is not separated.
- The margins are therefore measured on a plant that is saturating motors (pin 0.26-0.45 during the window): not a valid
  linear measurement. Consistent with the earlier model-only result of PM 25 deg / GM 4.3 dB (S40) being 'far below the linear model'.
- Suggested next step (not done): fix the yaw 43 Hz oscillation (yaw G1 205 vs the 222 without rotor spin inertia, or yaw
  rate-loop gain/filter), re-run the gate on a hover window with no injection (use --delay and a window ending before t0 = DLY
  after trigger), then re-fly.

## Commands
```
# params: S40 inj_{model_long,model_long_a010,measured_long}.params + 3 MC_INDI_G1 lines + SENS_BAR_AUTOCAL 0 -> inj_*_g1*.params
indi_project/docker/run.sh -n s47f1 -t 900 'python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --params indi_flight/results/stage2_s47/roll_m3a/inj_model_g1.params --out indi_flight/results/stage2_s47/roll_m3a/model_s1' > .../model_s1_stdout.log 2>&1
indi_project/docker/run.sh -n s47p1 -t 600 'bash indi_flight/results/stage2_s47/roll_m3a/post.sh model_s1 0.005'
```
post.sh runs checks.py <run> 0.005 20 3; pretest_gate.py <ulg> <md>; m3a_csv.py <ulg> 0 <csv> (injected axis is 0 = roll with
MC_INDI_INJ_AX 1); m3a_margins_pretest.py <csv>.

## UNVERIFIED
- Cause of the 43 Hz yaw oscillation (G1_Y value, yaw filter, or motor model): not tested.
- Whether the 1 rad/s roll response is linear closed-loop behaviour or saturation-driven.
- Linearity (amplitude 0.01), seed repeat, and measured-rotor-speed (--sim v2) variant: not flown.
- Min 1/abs(L) at arg L near -180 not computed (arg L is -142 to -148 near crossover, then passes -180 only around 8-9 Hz where GM is read).
- Gate window overlap with the injection is by its design (delay 15 s from airborne vs DLY 20 s trigger from not-landed, plus 30 s length); pre-injection-only gate not run.

# Follow-up S47 (H1 / H2)
Seed 1, speed 4, hover_long, indi_m3a, quad5in. No-injection stats from `noinj.py` over the airborne hover (first not-landed + 15 s,
30 s, 47.0-77.0 s; detrended rate std, FFT dominant frequency, pin = any motor <0.005 or >0.995). Params files `inj_*_a0.params`,
`inj_model_g1y215_a0.params`; stdout logs `<name>_stdout.log`.

Param differences inj_model_g1 vs inj_measured_g1 (only difference): `CA_R_W_MAX 2700` in measured (plus `--sim v2` rpm variant).
Both have MC_RATE_CTL_TYPE 1, INJ_* identical, G1 1757/1640/205, SENS_BAR_AUTOCAL 0. No other actuator-state parameter is set.
inj_measured_g1 vs S45 `a23_indi_g1y.params`: S45 has AMP 0, G1 1756/1599.49/215, no SENS_BAR_AUTOCAL; same CA_R_W_MAX 2700.

| flight | setup | roll std | pitch std | yaw std | yaw dom. freq | pin |
|---|---|---|---|---|---|---|
| F5 model_noinj | model-only, AMP 0 | 0.0237 | 0.0220 | 0.307 | 41.0 Hz | 0.365 |
| F6 measured_noinj | --sim v2, AMP 0 | 0.0361 | 0.0322 | 0.369 | 40.7 Hz | 0.522 |
| F7 measured_a001 | not flown (F6 not clean) | | | | | |
| F8 model_noinj_g1y215 | F5 with G1_Y 215 | 0.0193 | 0.0194 | 0.223 | 41.7 Hz | 0.193 |
| F9 s45_replay (extra) | S45 params exactly, --sim v2 | 0.0216 | 0.0192 | 0.336 | 41.0 Hz | 0.390 |
| S45 original log (same script) | | 0.0071 | 0.0075 | 0.0012 | 45 Hz | 0.000 |

run.json diff F9 vs S45 original: S45 ran at commit 7825fca2 on a DIRTY tree, F9 at e923ed0e clean; hover_thrust_estimate 0.1367 (S45)
vs 0.1939 (F9). Everything else equal apart from timestamps. The sitl binary was rebuilt 2026-11-16 09:11; src commits since S45 include
gz_bridge baro changes and f44674b399 (bench excitation in mc_indi_rate_control).

## Conclusion
1. H1 not supported: the 41 Hz yaw oscillation (pin 37-52 %) appears with model-only (F5) AND with --sim v2 (F6), so the actuator-state path is not the discriminator.
2. G1_Y 215 (F8) does not remove it (pin 19 %, yaw std 0.22), so the 5 % yaw G1 change is not the cause either; the S45 params replayed exactly (F9) also oscillate (pin 39 %).
3. The S45 clean hover does not reproduce on the current tree: hover thrust estimate differs (0.137 vs 0.194) and S45 was a dirty tree; the cause is likely a code or sim-model difference since 7825fca2 (not bisected, UNVERIFIED).
4. H2 not tested: F7 was gated on a clean F6; AMP 0.001 is moot until the no-injection hover is clean (injection amplitude is not the cause of the yaw oscillation, which exists at AMP 0).
5. Next: find the difference behind the hover-thrust shift (diff firmware/model between 7825fca2 dirty and HEAD, e.g. run S45 params on a worktree at 7825fca2).

# S47 orchestrator: yaw spin-up term G2 (closes A-25)
Correction to conclusion 3 above: there is NO source, model or binary change between 7825fca2 and HEAD
(`git log 7825fca2..HEAD -- src ROMFS Tools msg boards indi_flight/sim` empty; SITL binary built 09:11, before S45;
fresh rootfs per run). S45 (clean) and F9 (limit cycle) are the same configuration: the yaw loop is bistable, a
lightly damped mode near 41-45 Hz (A-24 tone in S45) that the take-off transient may or may not push into motor
saturation. Hover thrust estimate 0.194 in F9 is a consequence of 39 % pinned motors, not a plant change.

Mechanism: MC_INDI_G2_Y was 0. gz drives each rotor joint at w/10 (`rotorVelocitySlowdownSim` 10,
ref_airframe_check P9), so the rotor spin inertia reacts on the body with J_r = 5e-5/10 = 5e-6 kg m^2.
Linearised at hover (w_h = sqrt(0.61*9.81/4/1.5e-6) = 999 rad/s; k_m = 0.01267*1.5e-6 = 1.9e-8 N m s^2):
spin-up torque / drag-torque change = J_r s / (2 k_m w_h) = 0.132 s * s, so above 1.2 Hz the spin-up term dominates
and at 41 Hz the plant yaw effectiveness is ~34x what the G2=0 law assumes. G2_Y = G1_Y * 0.132 = 205*0.132 = 27.

Test (seed 1 and 2, model-only and `--sim v2`, AMP 0, params `inj_*_g1_g2_a0.params` = F5/F6 + `MC_INDI_G2_Y 27`;
`noinj.py` + `bench/pretest_gate.py`, output `g2_summary.txt`, `*_gate.md`):
| run | roll / pitch / yaw std rad/s | dominant | pin | gate |
|---|---|---|---|---|
| model_g2 s1 | 0.0051 / 0.0044 / 0.0063 | <0.4 Hz | 0 | PASS |
| measured_g2 s1 | 0.0052 / 0.0058 / 0.0183 | <0.4 Hz | 0 | PASS |
| model_g2_s2 s2 | 0.0045 / 0.0046 / 0.0134 | <0.4 Hz | 0 | PASS |
| measured_g2_s2 s2 | 0.0049 / 0.0061 / 0.0121 | <0.4 Hz | 0 | PASS |
Against F5/F6 (same seeds and paths, G2 0): yaw std 0.31-0.37, 41 Hz, pin 37-52 %. Commands as in the F5/F6 rows
with the new params files and out dirs `model_g2`, `measured_g2`, `model_g2_s2`, `measured_g2_s2`.
Note: the first parallel launch of model_g2 produced no output (two containers at once, cause not checked); it was
re-flown alone.
UNVERIFIED: G2 derivation second key pending (`results/stage2_s47/g2_second_key.md`); G2 varies as 1/w (operating
point); the 45 Hz tone (A-24) not re-checked by PSD with G2 27.
