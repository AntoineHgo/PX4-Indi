# A-31 wrench source (s66)
Version: gz-sim 8.15.0 (image px4-indi-sim, `gz sim --versions`). Source read from GitHub tag gz-sim8_8.15.0
(not installed in image; copies in session scratchpad src/).

## (1) One-step queue (systems/apply_link_wrench/ApplyLinkWrench.cc)
- OnWrench :318-331 pushes every message onto `newWrenches` (queue, no dedupe, no replace).
- PreUpdate :236-316: while queue non-empty (:273-299) each message -> `link.AddWorldWrench` (:289), so ALL messages received since
  last PreUpdate are SUMMED and applied in that ONE step. If paused: return before applying (:269) and messages stay queued.
- Link.cc AddWorldWrench: creates ExternalWorldWrenchCmd or ADDS to existing one (Link.cc:545-558).
- Physics.cc:4108-4112 clears the ExternalWorldWrenchCmd (`Data().Clear()`) after each step; Physics reads it at :2578. No accumulation across steps.
- Persistent: OnWrenchPersistent :335 `persistentWrenches.push_back` (a list, no dedupe). PreUpdate :301-315 adds every list entry each step.
  Repeating the same persistent message => a SECOND persistent wrench (adds, force doubles). Only /wrench/clear (:243-266, erases by entity) removes them.

## (2) Clock rate
- SimulationRunner.cc:1014 Step() -> :1024 PublishStats() -> clockPub.Publish (:563) with no throttle: /world/<w>/clock is published
  every physics step (also rootClockPub :567). World step 0.004 s (Tools/simulation/gz/worlds/default.sdf:5) => 250 steps/sim-s, ~1000 steps/wall-s at RTF 4.
- Delivery to disturbance.py is asynchronous (transport thread, Python callback, csv write); no step-locked handshake.
  Nominal: 1 message per step. Bursts/gaps are possible (UNVERIFIED, not measured).

## (3) Explanation
- Mechanism for a factor of exactly 2 is NOT proven by source alone. Nominal flow gives 1 message/step => 1x.
- Ruled out: double-loading the system (each run log shows a single `system add attempt 0: ... true`).
- Candidates, all UNVERIFIED:
  a) second publisher or second ApplyLinkWrench on same topic/partition (the 5 runs started concurrently at 22:14:23; if they share a gz partition
     and world name, every run's wrench is summed in every sim => ~Nx). gz.log has no "Listening to instantaneous" line, so load count not confirmed.
  b) clock messages queued/duplicated (/clock and /world/<w>/clock are both published, only the latter subscribed).
  c) Python callback lag at RTF 4 => bursts (2+ messages in one step: spikes; sum) followed by steps with none: explains the
     "loss for a moment" (gaps), and a mean >1 is impossible unless messages are duplicated, so (a) is the better 2x lead.
- Check: grep gz.log for ApplyLinkWrench load count, `gz topic -i -t /world/<w>/wrench` (publisher/subscriber count), and log per-step
  applied wrench count.

## (4) Recommended fix
- Use /world/<w>/wrench/persistent published ONCE per value change (not per clock tick), and /wrench/clear BEFORE each change (clear then
  republish), since persistent entries append. Persistent is applied every step in PreUpdate (:301-315), independent of RTF and delivery jitter.
- Note: clear is processed at the start of PreUpdate before... new persistent entries received in same cycle are pushed to the list
  independently; ordering clear vs. persistent within one cycle is not guaranteed (UNVERIFIED) => send clear, wait >=1 step, then publish.
- Alternative: model/world plugin computing wrench in PreUpdate from sim time (deterministic, step-locked); preferable for time-varying profiles.
- Persist the value in csv from the same source of truth; keep per-step publication only if deterministic count per step is verified.

## Orchestrator note (S66)
- Partition cross-talk is unlikely: `indi_project/docker/run.sh` sets no `--hostname` and no host network, so each
  container has its own hostname and so its own default GZ_PARTITION (hostname:user). UNVERIFIED: GZ_PARTITION env in
  the image (check `env | grep GZ_` in a container).
- Decisive tests for S67, in order: (1) payload_add flown ALONE (no parallel run), rpm^2 ratio in the window; (2) log
  per clock callback the sim time and count messages per physics step (2 per step would give 2x); (3) `gz topic -i -t
  /world/default/wrench` during a run; (4) speed 1 vs 4. Fix candidate: persistent topic on change + clear, or a
  step-locked plugin; second key either way.
