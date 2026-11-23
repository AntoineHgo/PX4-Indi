# G6 item 7 prep (S212): 60 corner runs C1-C6, un-identified state

Spec: GATES.md S208 amendment "G6 un-identified state (Q27 item 7)" (line 759-762) as reduced by S211b to the 60 corners:
"flown at `MC_INDI_ID_OK` 0 (gains x0.5, ACT_TC 0.05). Pass: item 1 (no LOC) in every valid run, item 2 (no sustained
oscillation) inside the identification-manoeuvre window. Item 2 elsewhere and items 3-6 reported."

## Orchestrator correction (supersedes the first version of this note)
Item 7 is the UN-identified state: ID_OK 0 AND ACT_TC 0.05. The drawn S211 r ACT_TC is the identified state and is NOT applied
(S211b wording "same S211 ACT_TC r draw" is read as "same plant draws"). So no actc block, no --samples, no --require-actc.

## Route (no code change)
- Draws: the seed-173 campaign draws, corners = run 240-299 (identical plant draws, gz_seed, sampler_seed, mode as the
  G3 re-fly corners run_000-059 whose source_run is 240-299; checked field by field on factors/seeds/mode for all 60).
  The chain flies a sub-range of the campaign: `start DIR 240 299`; run indices keep the campaign numbering 240-299.
- Params: `params_id0.params` = results/g5_freeze_s157/params.params (the freeze-10 G3 set) with MC_INDI_ID_OK 0 and
  MC_INDI_ACT_TC 0.05. The chain takes it via env G3_PARAMS (first start only, pinned in DIR/chain_params).

## Firmware: ID_OK 0
McIndiRateControl.cpp:98-99 calls indiEffectiveGainK(K, id_ok == 1): while ID_OK is not 1, K_R/K_P/K_Y are applied at 0.5x.
Nothing else reads the parameter. ACT_TC is not changed by it, hence it is set to 0.05 in the params file. Nothing in
g3_run.py, g3_chain.sh, run_validity.py, g3_checks*.py assumes ID_OK 1; run_scenario.py only does setdefault("MC_INDI_ID_OK","1"),
so the file's 0 is kept.

## Evidence (build_run on run 240-299, G3 freeze params vs params_id0)
Only difference in any field (argv, params, overrides, merged_params, applied, not_applied, notes), over all 60:
merged_params MC_INDI_ID_OK 1 -> 0 and MC_INDI_ACT_TC 0.033 -> 0.05. `actc` absent from every draw and from `applied`:
ACT_TC is not overridden per run (merged value 0.05 for all 60). `diff` of the params files: line 1 (comment), 16, 22.

## Halt-on-fail
The S211b halt rule is written for the G3 re-fly only; item 7 has no fail-fast rule. Not used.

## Item 2 scoring
No identification manoeuvre exists in these flights (injector off), so the "identification-manoeuvre window" is empty:
item 2 is scored over the whole flight (stricter than the gate text). Item 1 in every valid run; items 3-6 reported.

## Launch (after the G3 chain finished and the lock is free)
G3_PARAMS=indi_flight/results/g6_item7_s212/params_id0.params bash indi_flight/bench/g3_chain.sh start indi_flight/results/g6_item7_s212 240 299 --speed 4

## Unverified
- Not run: first start in a non-empty DIR and the 240 299 sub-range are read from the code only.
- Binary and docker image pins must still match the freeze-10 pins at launch.
- Speed 4 is copied from the G3 re-fly launch (the freeze-10 campaign speed was not re-checked).
