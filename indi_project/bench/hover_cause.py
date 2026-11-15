#!/usr/bin/env python3
"""Hover causal test (session 48, results/s2_hover_effort_cause.md sec. 4): motor-rate effort per seed and controller,
mean and ratio to pid_tuned, and the fraction of the window in which INDI used the measured torque.

Usage: hover_cause.py [RUNS_DIR] (default results/hover_cause/runs). Prints a Markdown table."""
import sys, json, os, numpy as np
from pyulog import ULog

runs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'results', 'hover_cause', 'runs')
ctrls = ['pid_tuned', 'indi_v2', 'indi_v2_wmax0']
seeds = [1, 2, 3]


def measured_in_use(d, win):
	try:
		u = ULog(os.path.join(d, 'flight.ulg'), ['indi_rate_status'])
	except Exception:
		return None
	if not u.data_list:
		return None
	s = u.data_list[0].data
	t = (s['timestamp'] - u.start_timestamp) * 1e-6
	sel = (t >= win['start_s']) & (t <= win['end_s'])
	return float(np.mean(s['measured_torque_in_use'][sel])) if sel.any() else None


eff = {}
print('| controller | ' + ' | '.join(f'seed {s}' for s in seeds) + ' | mean | ratio | measured torque in use |')
print('|---' * (len(seeds) + 4) + '|')
for c in ctrls:
	vals, use = [], []
	for s in seeds:
		d = os.path.join(runs, 'hover', c, f'seed{s}')
		try:
			m = json.load(open(os.path.join(d, 'metrics.json')))
		except (OSError, ValueError):
			vals.append(np.nan)
			continue
		vals.append(m['effort']['motor_rate_rms_per_s'])
		if c != 'pid_tuned':
			use.append(measured_in_use(d, m['window']))
	eff[c] = np.nanmean(vals)
	ratio = eff[c] / eff['pid_tuned']
	u = ', '.join('-' if x is None else f'{x:.2f}' for x in use) if use else '-'
	print(f'| {c} | ' + ' | '.join(f'{v:.4f}' for v in vals) + f' | {eff[c]:.4f} | {ratio:.2f} | {u} |')
