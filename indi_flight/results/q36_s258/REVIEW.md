# Independent review: INDI eRPM arming check (uncommitted working tree)

Counts: BLOCKER 0, MAJOR 1, MINOR 8. Nothing was built or run; all reasoning is from the code.

## Protocol check against commander (spec item 3)
- Request/reply id: reply.request_id = request.request_id (McIndiRateControl.cpp:~296); commander accepts only `_current_request_id == reply.request_id`
  and `registrationValid(registration_id)` (externalChecks.cpp update()). OK.
- Reply timing: commander drops a reply if `now > reply.timestamp + 300 ms`; the module stamps `now` at answer time, so OK. Commander flags a missing reply
  after REQUEST_TIMEOUT 50 ms, but a late reply from the right request still counts; unresponsive after >3 missed 300 ms cycles (>10 right after registering),
  and for a generic check (nav_mode_id == -1) the registration is removed, never flagged "unresponsive", so no failsafe path exists (checkAndReport only
  reports unresponsive modes with nav_mode_id != -1). OK for "must never trigger failsafe".
- Registration: request has register_arming_check only, register_mode false -> valid (ModeManagement.cpp:284). Cached resend by request_id makes retries idempotent.
  A new slot starts with a zeroed reply (can_arm_and_run false) until the first answer, so a fresh registration blocks arming immediately (conservative).
- Queues: RegisterExtComponentRequest/Reply 2, ArmingCheckReply 8, ArmingCheckRequest 1 (default). Loop `tries` pattern copies commander's; fine.
- Registration while armed: commander rejects (success=false) unless COM_MODE_ARM_CHK; module only registers while disarmed. Comment at McIndiRateControl.cpp:~249
  ("only takes registrations while disarmed") is inexact when COM_MODE_ARM_CHK=1 (MINOR, wording only).
- unregister message fields (name, arming_check_id, mode_id, mode_executor_id) match UnregisterExtComponent.msg; name "INDI rpm telemetry" (18) fits char[25].

## Answers
a) esc_status is consumed only in updateMeasuredTorque() (McIndiRateControl.cpp:166-221), called at the end of the gyro cycle inside
   `if (_vehicle_control_mode.flag_control_rates_enabled)` (Run, ~l.569), NOT in a state-independent place. It does not depend on armed. Disarmed in the normal
   user modes (Manual, Stab, Alt, Pos, Acro, Auto*, Descend; ModeUtil/control_mode.cpp) rates_enabled is true, so samples are fed disarmed. Where it is false
   (TERMINATION, OFFBOARD without matching setpoints, flags before the first commander publication) no sample is fed and the check refuses (never passes wrongly):
   correct direction but a hidden coupling. MINOR (McIndiRateControl.cpp Run, updateMeasuredTorque call site). Hardware assumption not verifiable here: the ESC driver
   must publish esc_status disarmed at >= ~50 Hz per motor, because IndiMeasuredTorque::SAMPLE_MAX_AGE_US (20 ms, IndiMeasuredTorque.hpp:74) applies
   regardless of MC_INDI_ERPM_TO. The dshot driver does request telemetry disarmed (DShot.cpp:383-401), so it is plausible.
b) Yes. updateArmingCheck() is called at McIndiRateControl.cpp:~424 for every gyro callback, before and independent of the rates_enabled / landed / armed
   branches, so every state (disarmed, armed, landed). Latency is one gyro period (ms) versus 50 ms / 300 ms in commander. If angular velocity stops, no
   replies are sent and commander removes the registration after ~1.2 s (no failsafe); with no gyro arming is denied anyway.
c) Disabled path returns can-arm (IndiErpmArmingCheck.cpp:~13 `!measured.enabled()`). enabled() = `_omega_max > 0 && _num_rotors > 0` (IndiMeasuredTorque.hpp:109):
   MC_INDI_W_MAX = 0 (this is the DEFAULT, mc_indi_rate_control_params.yaml:26) or no valid rotor effectiveness (non-rotor/failed geometry). It is a deliberate
   scope limit (rpm is unused there, in flight INDI already runs on its model), not a hole in intent, but it is a hole against the literal wording of requirement 1.
   MC_INDI_ERPM_TO is also documented "Only used when MC_INDI_W_MAX is set", consistent. MINOR: state it explicitly in the param/user docs. Also untested.
d) Ungated windows:
   - Boot: from module start until the first reply: registration retry 1 s + commander request cycle <= 300 ms, so ~1-1.5 s after the module starts
     (longer if commander starts later). Arming that early is blocked by the stock preflight checks in practice, but not by this check. MINOR.
   - Registration dropped by commander (stalled module > ~1.2 s, commander restart, all 8 slots full): module notices only after
     REQUEST_TIMEOUT = 3 s without requests (McIndiRateControl.cpp:~251), then re-registers; ungated for ~3-4 s and arming is possible. Using about 1 s would shrink the
     window (re-registration is idempotent through the cached reply). MINOR. If dropped while armed it cannot re-register until disarm; at disarm the stale
     timestamp makes it re-register on the next cycle.
   - Slot exhaustion: reply.success=false is silently retried every 1 s forever, no log, never gated. MINOR.
e) Armed behaviour: no change to control or setpoint publications. Added per cycle: 2 Subscription::update, one hrt_absolute_time, a few compares
   (hot path at gyro rate, negligible but non-zero), plus an arming_check_reply publication every 300 ms while armed. evaluate() returns can-arm when armed, and
   registration/event/compute code is skipped, so a false reply while armed is impossible except one race: a request answered false in the gyro cycle just before
   flag_armed becomes true. Commander only uses can_arm for arming decisions (Commander.cpp:723, 2103, 2640), no failsafe or disarm. Effect: cosmetic at most. IndiMeasuredTorque.compute() adds one OR in the
   invalid branch (no behaviour change). OK.
f) Tests (IndiErpmArmingCheckTest.cpp), each reasoned from the code:
   - AllMotorsFreshCanArm: fails if fresh samples are refused or mask nonzero. Valid.
   - MotorWithoutTelemetry: fails if a never-reported motor or setMotorOffline (clears online/has_value) is not refused, and if motor_unusable_mask is not set. Valid.
   - StaleSample: first half (50 ms old) fails if the 20 ms age limit or the per-motor mask is lost; second half (5 ms old, 2 ms timeout) fails if the
     MC_INDI_ERPM_TO check is dropped. Valid.
   - NeverRefusesWhileArmed: fails if `armed` is ignored. Valid.
   Gaps (MINOR): no test of the disabled path (c), numRotors/mask for 12 motors, nor of any of the commander glue in updateArmingCheck (reply fields,
   registration retry/timeout, armed reply true). The glue is unexercised outside SITL.

## Findings
MAJOR
1. User-visible behaviour change without documentation: MC_INDI_ERPM_TO / MC_INDI_W_MAX descriptions (mc_indi_rate_control_params.yaml:14-26, 162-176) still say
   a stale/missing rpm only falls back to the actuator model; they do not say arming is now refused. No change under docs/en or the yaml in the diff. A
   user with a working vehicle and a flaky/disabled ESC telemetry will see "arming denied" with no documented cause or remedy (set MC_INDI_W_MAX 0).

MINOR
2. McIndiRateControl.cpp:~251: 3 s own-timeout gives a ~3-4 s ungated window after a dropped registration (see d).
3. McIndiRateControl.cpp:~262: silent endless retry when the commander refuses (success=false, slots full); no log (see d).
4. McIndiRateControl.cpp:~290-305: event is sent directly with events::send every 10 s as Error while disarmed, not through the reply's events (so not tied
   to an arming attempt and not shown as the reason in the arming denial); bit mask printed as a decimal number ("bit mask {1}"). Consistent with other
   mc_indi modules' use of events::send, but noisy for a vehicle that is simply left on the bench.
5. No hysteresis: the verdict is a snapshot at each 300 ms request using a hard 20 ms sample age; telemetry jitter just above 20 ms makes the reply flip, so
   arming can be refused intermittently.
6. Samples are fed only under flag_control_rates_enabled (a); refusal when not set.
7. Comment at McIndiRateControl.cpp:~249 inexact with COM_MODE_ARM_CHK; IndiErpmArmingCheck.cpp "@file" has no description line.
8. Disabled path (c) returns can-arm and is untested; hole against literal requirement 1 when MC_INDI_W_MAX = 0 (default).
9. Test coverage gaps in (f).

Style (rule F-10): no project ids or bookkeeping words found in the diff or the three new files (only "COPYRIGHT OWNER" in the licence block). Names carry units
(now_us, timeout_s) and follow PX4 conventions (_member, camelCase); file headers match the existing ones; events usage matches other modules. No finding.
