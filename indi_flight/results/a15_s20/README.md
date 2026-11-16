# A-15 sample-gap analysis

Run: `python3 indi_flight/bench/a15_gaps.py indi_flight/results/a12_fix_s18/pretest_truth_topics/hover/flight.ulg --out indi_flight/results/a15_s20/README.md`. Topic `vehicle_*` groundtruth topics all present; no topic skipped. Full gap table (10,590 merged rows) is below.

## Conclusion

1. The logger recorded no drops: pyulog `ULog.dropouts` is empty (no logging_dropout messages), so the gaps are not logger-reported drops.
2. The three groundtruth topics have 7,565 to 7,735 gaps each, 97-100% of them at the same times as each other but 0-8% at controller-topic gap times; every gap is also present in their own `timestamp_sample`, so the sample timestamps themselves skip, which points to the publishers.
3. Controller topics mostly skip at different times: sensor_gyro's 10 gaps match no other controller topic, actuator_motors' 787 gaps match vehicle_angular_velocity only 38%, and only vehicle_angular_velocity, vehicle_torque_setpoint and actuator_motors overlap strongly (74-98%, as shown in the pairwise matrix).


- Log: `results/a12_fix_s18/pretest_truth_topics/hover/flight.ulg`
- Log start timestamp: 30016250 us. First 1 s ignored.
- Gap threshold: dt > 1.9 ms (nominal period 1.25 ms).
- Merge window for coincident gap times: 1.0 ms.
- Topics not in log: none

## Per-topic summary

| topic | samples (after 1 s) | median period (ms) | gap intervals | missing samples (est.) | timestamp_sample field | timestamp_sample gap intervals | of those, within 1 ms of a timestamp gap | note |
|---|---|---|---|---|---|---|---|---|
| sensor_gyro | 58948 | 1.250 | 10 | 10 | yes | 10 | 10 |  |
| vehicle_angular_velocity | 58948 | 1.250 | 325 | 325 | yes | 16 | 16 |  |
| actuator_motors | 58952 | 1.250 | 787 | 787 | yes | 12 | 12 |  |
| vehicle_torque_setpoint | 58949 | 1.250 | 429 | 429 | yes | 15 | 15 |  |
| esc_status | 57588 | 1.250 | 2824 | 2933 | no | - | - |  |
| vehicle_attitude_groundtruth | 51393 | 1.250 | 7565 | 7571 | yes | 7565 | 7565 |  |
| vehicle_angular_velocity_groundtruth | 51223 | 1.250 | 7735 | 7741 | yes | 7735 | 7735 |  |
| vehicle_local_position_groundtruth | 51259 | 1.250 | 7699 | 7705 | yes | 7699 | 7699 |  |

Gap times merged across topics: 10590 rows. Rows where one topic has a gap: 2206. Rows where two or more topics have a gap at the same time: 8384.

## Gap table

10,590 rows, not committed; regenerate with the command above.

## Pairwise coincidence

Cell = share of the row topic's gap times that have a gap in the column topic within 1 ms.

| row topic (gaps) | sensor_gyro | vehicle_angular_velocity | actuator_motors | vehicle_torque_setpoint | esc_status | vehicle_attitude_groundtruth | vehicle_angular_velocity_groundtruth | vehicle_local_position_groundtruth |
|---|---|---|---|---|---|---|---|---|
| sensor_gyro (10) | 100% | 0% | 0% | 0% | 0% | 20% | 20% | 20% |
| vehicle_angular_velocity (325) | 0% | 100% | 93% | 98% | 78% | 5% | 5% | 5% |
| actuator_motors (787) | 0% | 38% | 100% | 51% | 78% | 2% | 2% | 2% |
| vehicle_torque_setpoint (429) | 0% | 74% | 94% | 100% | 77% | 4% | 4% | 4% |
| esc_status (2824) | 0% | 9% | 22% | 12% | 100% | 8% | 8% | 8% |
| vehicle_attitude_groundtruth (7565) | 0% | 0% | 0% | 0% | 3% | 100% | 99% | 100% |
| vehicle_angular_velocity_groundtruth (7735) | 0% | 0% | 0% | 0% | 3% | 97% | 100% | 99% |
| vehicle_local_position_groundtruth (7699) | 0% | 0% | 0% | 0% | 3% | 98% | 100% | 100% |

## Logger dropouts (pyulog `ULog.dropouts`)

No logging_dropout messages in this log.

