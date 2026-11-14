#!/usr/bin/env python3
"""Hover motor-rate effort of the v3 candidates vs pid_tuned (session 47).

Reads results/v3_hover_effort/runs (seeds 2-5) and the seed-1 hover runs of results/v3_screen_yaw/runs
(v3_tb0.3 = k2.733_c1.665 there: same params, yaw values written explicitly). Prints a Markdown table of
motor_rate_rms_per_s per seed, the mean over seeds, and the ratio of means to pid_tuned (V' criterion 4: <= 1.5).
Usage: python3 bench/v3_hover_effort.py [project_dir]
"""
import json
import pathlib
import statistics
import sys

P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1])
CONFIGS = ['pid_tuned', 'v3_tb0', 'v3_tb0.3', 'k2.733_c3.0', 'k4.0_c3.0']
SEED1_ALIAS = {'v3_tb0.3': 'k2.733_c1.665'}


def effort(path):
    if not path.is_file():
        return None
    return json.loads(path.read_text())['effort']['motor_rate_rms_per_s']


rows = {}
for c in CONFIGS:
    vals = {1: effort(P / 'results/v3_screen_yaw/runs/hover' / SEED1_ALIAS.get(c, c) / 'seed1/metrics.json')}
    for s in (2, 3, 4, 5):
        vals[s] = effort(P / f'results/v3_hover_effort/runs/hover/{c}/seed{s}/metrics.json')
    rows[c] = vals


def mean(vals, seeds):
    v = [vals[s] for s in seeds if vals[s] is not None]
    return statistics.mean(v) if v else None


ref25 = mean(rows['pid_tuned'], (2, 3, 4, 5))
ref15 = mean(rows['pid_tuned'], (1, 2, 3, 4, 5))
print('| config | s1 | s2 | s3 | s4 | s5 | mean s2-5 | ratio s2-5 | ratio s1-5 |')
print('|---|' + '---|' * 8)
for c, vals in rows.items():
    cells = ['-' if vals[s] is None else f'{vals[s]:.4f}' for s in (1, 2, 3, 4, 5)]
    m25, m15 = mean(vals, (2, 3, 4, 5)), mean(vals, (1, 2, 3, 4, 5))
    r25 = f'{m25 / ref25:.2f}' if m25 and ref25 else '-'
    r15 = f'{m15 / ref15:.2f}' if m15 and ref15 else '-'
    print(f'| {c} | ' + ' | '.join(cells) + f" | {m25 if m25 is None else f'{m25:.4f}'} | {r25} | {r15} |")
