# G6 item 7 chain launch (S243)

Command (from repo root), run detached by the script (systemd-inhibit + setsid nohup):

    G3_PARAMS=indi_flight/results/g6_item7_s212/params_id0.params bash indi_flight/bench/g3_chain.sh start indi_flight/results/g6_item7_s212 240 299 --speed 4

No --exclude-sat-weak, no --halt-on-fail, no --samples.

Launched: 2026-11-26 19:54:51 (+01:00).

PIDs:
- chain (bash _run): 1997213, session/sid 1997203 (systemd-inhibit wrapper)
- waiter: none separate; the start command exited rc=0 after spawning the chain.
- first flight at launch: timeout 1997333 -> docker run 1997334 (container px4-indi-g3c_240)

Pins checked before launch:
- binary build/px4_sitl_default/bin/px4 sha256 903eae63ce... (FREEZE-10 gate binary): OK
- docker image px4-indi-sim id 85779446d1... equals campaign DIR chain_image_id: OK
- params file is the one in PREP.md (params_id0.params, ID_OK 0, ACT_TC 0.05): OK
- no other chain: lock indi_flight/logs/flight_chain.lock not held, no g3/px4/gz processes before launch.
- Not built anything.

First status (19:55 check):
    running; pid 1997213 alive; lock held: yes
    campaign 240-299 (flying 240-299): done 0, failed 0, remaining 60; current idx 240 flying
    binary 903eae63ceb1..., speed 4.0, mean cycle 140.0 s, ETA 2026-11-26 22:14:51

Check status:
    bash indi_flight/bench/g3_chain.sh status indi_flight/results/g6_item7_s212 | tail -n 20
Log: indi_flight/results/g6_item7_s212/chain.log
Stop (only if needed, not done): bash indi_flight/bench/g3_chain.sh stop indi_flight/results/g6_item7_s212

## Resume

- Reason: chain stopped after run 240 because bench/g3_checks.py and g3_checks_key2.py changed (Q34 item 5 "A and B" rule, committed). Hashes re-pinned, CHAIN_HALTED removed.
- New hashes (chain_freeze.sha256 lines 21-22 only):
  - g3_checks.py 20487ca205b422cd5760a2baf02c9413e06a163c6863a0c1de97fdd05df299b4
  - g3_checks_key2.py 3a757a2dfcb3422fed53df525e8c6c5242a9632055dbde2f693d6a841f304999
- Verify: sha256sum -c chain_freeze.sha256 passes (rc 0). Run 240 not re-flown (scored, done 1).
- Resumed: 2026-11-26 ~20:02 (binary 903eae63ceb1..., speed 4.0 pinned).
- Chain pid: 2025254 (lock held).
- Status: running; campaign 240-299, current idx 241 flying, remaining 59; scored 1 (key 1 pass, key 2 pass). ETA 2026-11-26 21:18.
