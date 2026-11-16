# A-16: actuator_motors / esc_status timestamp gaps and zero-dt pairs

## Inputs

- Log: `results/a15_s21/hover/flight.ulg` (PX4 ULog, controller 800 Hz, nominal dt 1.25 ms)
- Window: first second skipped. Analysed `[31.020 s, 101.7625 s]` (70.743 s), using the
  common end (minimum of the three topics' last timestamps).
- Expected slots = window / 1.25 ms + 1 = 56595.0.
- Topics (multi_id 0): `actuator_motors`, `esc_status`, `sensor_gyro`.

## Command

```
python3 bench/a16_check.py results/a15_s21/hover/flight.ulg results/a16_s22
```

pyulog was importable on the host, so Docker was not used. The script writes
`results/a16_s22/a16_check.json` (full metrics) and `results/a16_s22/a16_table.md`.

## Definitions

- Gap: `dt > 1900 us`. Missing slots: sum of `round(dt / 1250) - 1` over gaps.
- Zero-dt pair: `dt == 0`. Identical means all value fields equal (timestamps and padding
  excluded). Different means at least one value field differs.
- "Gap before pair": a gap in the two diffs immediately before the pair (within 2 samples).
- "Gap->zero": fraction of gaps followed by a zero-dt pair within 2 diffs.
- `unique + missing vs exp` = (distinct timestamps + missing slots) / expected - 1. A value
  near 0 means every slot is accounted for.

## Results

| topic | field | n | n vs exp | unique+missing vs exp | gaps | missing slots | zero pairs | identical | different | gap before pair | gap->zero | dt==1250 frac |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| actuator_motors | timestamp | 56581 | -0.02% | +0.00% | 786 | 790 | 776 | 0 | 776 | 0.976 | 0.963 | 0.9859 |
| actuator_motors | timestamp_sample | 56580 | -0.03% | +0.00% | 12 | 15 | 0 | 0 | 0 | n/a | n/a | 0.9998 |
| esc_status | timestamp | 55529 | -1.88% | -0.00% | 2530 | 2625 | 1560 | 1184 | 376 | 0.926 | 0.583 | 0.9531 |
| esc_status | timestamp_sample | n/a (field absent) | | | | | | | | | | |
| sensor_gyro | timestamp | 56586 | -0.02% | +0.00% | 7 | 9 | 0 | 0 | 0 | n/a | n/a | 0.9999 |
| sensor_gyro | timestamp_sample | 56586 | -0.02% | +0.00% | 7 | 9 | 0 | 0 | 0 | n/a | n/a | 0.9999 |

Additional facts:

- actuator_motors: all 776 zero-dt pairs have different control values. The timestamp_sample
  step across every pair is exactly 1250 us. Median `timestamp - timestamp_sample` at the second
  sample of each pair is 0 us.
- esc_status: `counter` never changes between consecutive samples with dt > 0, so it cannot
  identify publishes. Of the 1560 pairs, 1184 have all value fields equal (duplicate-like,
  ESC telemetry not updated) and 376 differ, in `esc_rpm` only.
- No negative dt in any topic.

## Verdict

**actuator_motors: (a) late-publish pairing, no duplicates, no loss.**

- Every zero-dt pair (776/776) has different values, so none is a duplicate publish.
- 97.6% of zero-dt pairs have a gap within the 2 preceding diffs. 96.3% of gaps are followed
  by a zero-dt pair within 2 diffs.
- The count is within 0.03% of expected, and unique + missing slots match expected to 0.00%.
  Nothing is lost in the net count.
- The timestamp_sample step across each pair is always 1250 us, so each pair is two distinct
  controller samples. The second sample of each pair has `timestamp == timestamp_sample`.
  The first sample's offset was not printed. The pattern is consistent with the first sample
  carrying the publish stamp of the next sample, i.e. a one-period late publish.
- Residual real loss on the controller timebase is 15 missing slots in timestamp_sample
  (0.03%), which is negligible.

**esc_status: mixed (duplicates plus a real rate deficit), not a 800 Hz stream.**

- The count is 1.88% below expected, outside the 0.5% tolerance. The unique + missing
  slots still match expected, so the deficit is a lower effective publish rate of ESC telemetry,
  not a logger drop.
- 76% of its zero-dt pairs are identical in every field, so they behave like duplicate publishes.
  The remaining 24% are late-publish pairs.
- It has no timestamp_sample field.

**sensor_gyro (reference):** 7 gaps, 9 missing slots (0.016%), no zero-dt pairs. This is
the clean baseline: the sensor stream is effectively complete.

**Controller-rate metrics:** yes, use `actuator_motors.timestamp_sample` (or sensor_gyro
timestamps). Using `actuator_motors.timestamp` gives false gap and dt-zero counts. Do not use
`esc_status` for controller-rate metrics at all: it is not an 800 Hz stream, and its timestamp
has duplicates and a real rate deficit.
