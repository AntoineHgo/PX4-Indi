# S103 scope: POSCTL thrust-gap pre-test (G5)

Read-only scoping. No file modified except this one. Line numbers from the working tree at HEAD 1218bf5a7e.

## 1. How run_scenario.py handles mode="stick"

- `indi_flight/bench/run_scenario.py:91` `STICK_MAIN_MODE = {"altctl": 2, "posctl": 3, "acro": 5, "stabilized": 7}`. POSCTL is already a supported `--stick-mode` value; no flag or key is needed.
- `run_scenario.py:648-652` `--stick-mode` (choices = STICK_MAIN_MODE keys). Help text: MANUAL_CONTROL streamed at 50 Hz sim time, COM_RC_IN_MODE 1, mode switched by MAV_CMD_DO_SET_MODE after the hover.
- `run_scenario.py:674` gate: `--stick-mode` must be set iff scenario mode is "stick", and not combined with `--sched`.
- `run_scenario.py:758` `STICK_PARAMS` overlaid on BASE_PARAMS (COM_RC_IN_MODE 1, COM_RCL_EXCEPT 7, MPC_Z_VEL_MAX_UP/DN, MAN_DEADZONE 0), lines 92-93.
- `run_scenario.py:821-825` stick path: 50 Hz grid, neutral samples from `stick_profile.neutral_sample(a.stick_mode, thr0)`, meta["stick"] records main_mode. `run_scenario.py:478-480` `send_stick` logs sticks.
- `indi_flight/bench/stick_profile.py:14` VELOCITY_MODES = ("altctl", "posctl"); `:61-63` neutral_sample gives z=500 (zero climb rate) for both. Centred x/y/yaw means POSCTL holds position; ALTCTL holds only altitude. This is the only behavioural difference the runner passes to PX4.
- The mode-switch call site (DO_SET_MODE) was not located by grep; `run_scenario.py:363` is the generic command_long_send. UNVERIFIED that it sends custom_mode 3 << 16 for posctl, though STICK_MAIN_MODE implies it.

## 2. Minimal change for POSCTL

Scenario is `indi_flight/bench/scenarios.py:185-188`. Add after line 188 (no runner change):

```python
SCENARIOS["s5_gap085_posctl"] = dict(mode="stick", axis=None, traj=ZSINE_O6,
                                     segments=[("settle", 15.0, 0.0), ("up", 5.0, 0.0), ("hold", 40.0, 0.0)],
                                     motor_fault=dict(segment="up", motors=[0, 1, 2, 3], thrust_scale=0.85))
```

Runner: none. Only the `--stick-mode posctl` argument differs. The ALTCTL path is untouched.

Caveat: POSCTL needs a valid local position estimate in SITL; the runner's `hold_pos_ned` (used by s5_gap_check.py) should then be the true hold point. UNVERIFIED that POSCTL flies cleanly on this build.

## 3. Command used for the ALTCTL flight (B)

Source: `indi_flight/results/stage5_s98/fly.sh:5` (and `README.md:10`). Shown with paths relative to the repo root:

```
indi_project/docker/run.sh -n s98b -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario s5_gap085_altctl --stick-mode altctl --controller indi_s98 --model quad5in --seed 1 --speed 4 --sim v2 --params $D/gap.params --out $D/B_altctl/run > $D/B.stdout.txt 2>&1
```

`$D` = `indi_flight/results/stage5_s98` (README). For POSCTL, replace `s5_gap085_altctl` with `s5_gap085_posctl`, `--stick-mode altctl` with `--stick-mode posctl`, and the `--out` folder (e.g. `G5_posctl/run`). Keep `gap.params` (= stage5_s70/gap.params).

Note: `indi_project/docker/run.sh` existence was not checked.

## 4. Metric / check for the standing z error

- `indi_flight/bench/s5_gap_check.py` (listed at bench/ grep line 75): z error over [ev+10, ev+20] s, mean/std; last 10 s; max abs dev; settle time. Used on the S98 run; works unchanged on stick runs per README.md:7.
- `indi_flight/bench/pretest_gate.py` (bench/ line 66): run as `pretest_gate.py <run>/flight.ulg <dir>/gate.md`. Its window [47, 77) s includes the motor fault at ~71 s, so all S98 flights FAILED on rate RMS (README.md:30 calls this a window artefact). Do not use it as a go/no-go without fixing the window.
- Reference values from README.md:14-16 (S98, seed 1): ALTCTL z err [ev+10,ev+20] 0.035 / 0.014 m; A offboard 0.003 / 0.023 m; prediction without compensation 0.368 m.

## Flags

- UNVERIFIED: POSCTL flight not run; no evidence it passes the gate.
- UNVERIFIED: whether the INDI z-only stage (MC_INDI_POS_EN) gates on mode; S98 never logged the stage directly (README.md:20).
- UNVERIFIED: DO_SET_MODE custom_mode encoding (see section 1).
- Single seed (seed 1); S98 differences of 0.01-0.04 m not significant (README.md:25).
