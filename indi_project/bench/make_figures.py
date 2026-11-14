#!/usr/bin/env python3
"""Regenerate every report figure from recorded data (no simulation).
usage (from the repo root, no arguments):  python3 indi_project/bench/make_figures.py
Writes PNGs (dpi 150) into indi_project/report/figures/. Loading helpers and metric keys are shared with
bench/summarize_seeds.py (imported by file path). See report/figures/README.md.
Each figure prints the plotted numbers and the comparison with the reference markdown tables in results/;
a relative disagreement above 2 % is flagged DISCREPANCY."""
import glob
import importlib.util
import json
import os
import statistics
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
RUNS = os.path.join(PROJ, 'results', 'runs')
OUT = os.path.join(PROJ, 'report', 'figures')
os.makedirs(OUT, exist_ok=True)

_spec = importlib.util.spec_from_file_location('summarize_seeds', os.path.join(HERE, 'summarize_seeds.py'))
ss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ss)
get, load = ss.get, ss.load

PID, INDI = 'pid_default', 'indi_tuned'
C_PID, C_INDI = '#4C78A8', '#D1495B'          # one colour per controller, used in every figure
TOL = 0.02
DISCREPANCIES = []

plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.alpha': 0.25, 'grid.linewidth': 0.5,
                     'savefig.bbox': 'tight', 'figure.dpi': 100})

ATT = 'attitude_tracking.rotation_angle_rms_deg'
EFF = 'effort.motor_rate_rms_per_s'
ROLLRATE = 'rate_tracking.roll_rms_rad_s'
POS3D = 'trajectory.rms_3d_m'

# scenario, label, primary-metric key, metric description, reference INDI/PID (mean-of-means, from the md tables),
# reference effort ratio, source of reference, seeds used for the reference (None = all)
SCEN = [
    ('com_shift', 'com_shift', ATT, 'attitude RMS', 0.16, 1.09, 'heldout_s14.md', None),
    ('gust_diag', 'gust_diag', ATT, 'attitude RMS', 0.57, 1.13, 'heldout_s14.md', None),
    ('gust_x', 'gust_x', ATT, 'attitude RMS', 0.60, 0.89, 'heldout_s14.md', None),
    ('payload_add', 'payload_add', ATT, 'attitude RMS', 0.72, 1.01, 'heldout_s14.md', None),
    ('mismatch_inertia', 'mismatch_inertia', ATT, 'attitude RMS', 0.88, 1.27, 'heldout_s14.md', None),
    ('step_diag', 'step_diag', ATT, 'attitude RMS', 0.92, 0.94, 'heldout_s14.md', None),
    ('motor_loss_0', 'motor_loss_0', ATT, 'attitude RMS', 10.297 / 9.05, 0.5093 / 0.39233,
     't8_motor_loss_s13.md (means of seeds 1-3, computed by hand)', {1, 2, 3}),
    ('mismatch_combined_att', 'mismatch_comb._att', ATT, 'attitude RMS', 0.91, 3.08, 'heldout_h5_s15.md / acceptance_s15.md', None),
    ('mismatch_combined_rate', 'mismatch_comb._rate', ROLLRATE, 'roll-rate RMS', 1.58, 1.09, 'heldout_h5_s15.md', None),
    ('traj_lemniscate', 'traj_lemniscate', POS3D, '3D position RMS', 0.95, None, 'heldout_s15.md', None),
    ('traj_circle_fast', 'traj_circle_fast', POS3D, '3D position RMS', 0.73, None, 'heldout_s15.md', None),
]


def seed_of(m, name):
    return m.get('seed', name)


def paired(scen, key, seeds=None, runs_filter=None):
    """Per-seed (pid, indi) pairs, paired by (seed number, run-dir name). Returns list of (seed, pid, indi)."""
    ra, rb = load(RUNS, scen, PID), load(RUNS, scen, INDI)
    out = []
    for name in sorted(set(ra) & set(rb)):
        s = seed_of(ra[name], name)
        if seeds is not None and s not in seeds:
            continue
        a, b = get(ra[name], key), get(rb[name], key)
        if a is not None and b is not None:
            out.append((s, a, b))
    return out


def flag(fig, name, mine, ref, src):
    if ref is None:
        print(f"  {name}: plotted {mine:.4f}, no reference in md")
        return
    rel = abs(mine - ref) / abs(ref)
    tag = 'ok' if rel <= TOL else 'DISCREPANCY'
    print(f"  {name}: ratio of means {mine:.3f} vs md {ref:.3f} ({src}) -> {tag} ({rel * 100:.1f} %)")
    if rel > TOL:
        DISCREPANCIES.append((fig, name, mine, ref, src))


def ratio_figure(fname, metric_idx, ylabel, title_note):
    """metric_idx: 0 -> primary tracking metric, 1 -> effort."""
    print(f"\n== {fname}")
    cols, missing = [], []
    for scen, label, pkey, desc, ref_att, ref_eff, src, rseeds in SCEN:
        key = pkey if metric_idx == 0 else EFF
        ref = ref_att if metric_idx == 0 else ref_eff
        pr = paired(scen, key)
        if not pr:
            missing.append(scen)
            continue
        ratios = [b / a for _, a, b in pr if a > 0]
        if not ratios:
            missing.append(scen + ' (zero PID baseline)')
            continue
        rm = statistics.mean([b for _, _, b in pr]) / statistics.mean([a for _, a, _ in pr])
        refpr = [p for p in pr if rseeds is None or p[0] in rseeds]
        rm_ref = statistics.mean([b for _, _, b in refpr]) / statistics.mean([a for _, a, _ in refpr])
        print(f"{scen} [{desc if metric_idx == 0 else 'motor-rate RMS'}] n={len(ratios)}: "
              f"median paired ratio {statistics.median(ratios):.3f}, range {min(ratios):.3f}-{max(ratios):.3f}")
        flag(fname, scen, rm_ref, ref, src)
        cols.append((label, ratios))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    rng = np.random.default_rng(0)
    for i, (label, ratios) in enumerate(cols):
        med = statistics.median(ratios)
        ax.bar(i, med - 1, bottom=1, width=0.62, color=C_INDI, alpha=0.30, lw=0)
        ax.hlines(med, i - 0.31, i + 0.31, color=C_INDI, lw=2)
        ax.plot(i + rng.uniform(-0.18, 0.18, len(ratios)), ratios, 'o', ms=3, color=C_INDI, mec='white', mew=0.4)
        ax.text(i, max(ratios) * 1.12, f"{med:.2f}", ha='center', va='bottom', fontsize=7.5)
    ax.axhline(1, color=C_PID, lw=1.5, label='PID default = 1')
    ax.legend(frameon=False, loc='upper left', fontsize=8)
    ax.set_yscale('log')
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c[0] for c in cols], rotation=35, ha='right')
    ax.set_ylabel(ylabel)
    ax.set_xlim(-0.6, len(cols) - 0.4)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.grid(axis='x', visible=False)
    ax.margins(y=0.12)
    lo, hi = ax.get_ylim()
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks([t for t in (0.1, 0.2, 0.3, 0.5, 0.7, 1, 1.5, 2, 3, 4, 5) if lo <= t <= hi])
    ax.set_ylim(lo, hi)
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)
    return missing


def fig_attitude_ratio():
    return ratio_figure('fig_attitude_ratio.png', 0, 'INDI / PID tracking error\n(log scale, <1 = INDI better)', '')


def fig_effort_ratio():
    return ratio_figure('fig_effort_ratio.png', 1, 'INDI / PID motor-rate RMS\n(log scale, <1 = INDI less effort)', '')


# ---- figure 3: ACT_TC sweep -------------------------------------------------------------------------------------
SWEEP_REF = {  # from results/act_tc_sweep_s17.md: (roll-rate RMS rad/s, motor-rate RMS 1/s)
    'pid_default': (0.086, 0.544), 0.33: (0.129, 0.788), 0.5: (0.128, 0.690), 0.67: (0.133, 0.678),
    1.0: (0.138, 0.646), 1.5: (0.143, 0.605), 2.0: (0.152, 0.609), 3.0: (0.161, 0.596)}


def fig_act_tc_sweep():
    fname = 'fig_act_tc_sweep.png'
    print(f"\n== {fname}")
    base = os.path.join(RUNS, 'step_roll')

    def vals(ctrl):
        out = []
        for f in sorted(glob.glob(os.path.join(base, ctrl, 'seed*_x4', 'metrics.json'))):
            m = json.load(open(f))
            out.append((get(m, ROLLRATE), get(m, EFF)))
        return out
    dirs = {float(os.path.basename(d)[len('indi_act'):]): os.path.basename(d)
            for d in glob.glob(os.path.join(base, 'indi_act*'))}
    facs = sorted(dirs)
    data = {f: vals(dirs[f]) for f in facs}
    pid = vals(PID)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax, j, yl in ((axes[0], 0, 'roll-rate RMS (rad/s)'), (axes[1], 1, 'motor-rate RMS (1/s)')):
        xs = [f for f in facs if data[f]]
        mean = [statistics.mean(v[j] for v in data[f]) for f in xs]
        for f in xs:
            ax.plot([f] * len(data[f]), [v[j] for v in data[f]], 'o', ms=3, color=C_INDI, alpha=0.5, mec='none')
        ax.plot(xs, mean, '-o', ms=4, color=C_INDI, label='INDI (seed mean)')
        pm = statistics.mean(v[j] for v in pid)
        ax.axhline(pm, color=C_PID, lw=1.5, label='PID default (seed mean)')
        ax.axvline(1.0, color='0.6', lw=0.8, ls=':')
        ax.set_xscale('log')
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{x:g}" for x in xs], fontsize=7.5)
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_xlabel('MC_INDI_ACT_TC factor f (1 = frozen, 0.0114 s)')
        ax.set_ylabel(yl)
        ax.set_ylim(bottom=0)
        name = yl.split(' (')[0]
        for f, m_ in zip(xs, mean):
            flag(fname, f"{name} f={f:g}", m_, SWEEP_REF[f][j], 'act_tc_sweep_s17.md')
        flag(fname, f"{name} PID", pm, SWEEP_REF['pid_default'][j], 'act_tc_sweep_s17.md')
        print(f"  {yl}: PID {pm:.3f}; INDI " + ', '.join(f"f={f:g}:{m_:.3f}" for f, m_ in zip(xs, mean)))
    axes[0].legend(frameon=False, fontsize=7.5, loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)


# ---- figure 4: roll-rate time series ------------------------------------------------------------------------------
def fig_timeseries():
    fname = 'fig_rate_timeseries.png'
    print(f"\n== {fname}")
    try:
        from pyulog import ULog
    except ImportError:
        print('  pyulog not installed: figure skipped')
        return 'pyulog missing'
    scen = 'mismatch_combined_rate'
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.4), sharex=True)
    for ax, ctrl, col, lab in ((axes[0], PID, C_PID, 'PID default'), (axes[1], INDI, C_INDI, 'INDI tuned')):
        runs = load(RUNS, scen, ctrl)
        name = next((n for n in runs if seed_of(runs[n], n) == 1), None)
        if name is None:
            return 'no seed 1'
        m = runs[name]
        t0, t1 = m['window']['start_s'], m['window']['end_s']
        ulg = ULog(os.path.join(RUNS, scen, ctrl, name, 'flight.ulg'))
        d = {x.name: x.data for x in ulg.data_list}
        av, sp = d['vehicle_angular_velocity'], d['vehicle_rates_setpoint']
        t_av = av['timestamp'] / 1e6
        t_sp = sp['timestamp'] / 1e6
        # metrics window start/end are in the same (log, seconds) time base as the ULog timestamps
        ax.plot(t_sp - t0, np.degrees(sp['roll']), color='0.35', lw=1, label='setpoint')
        ax.plot(t_av - t0, np.degrees(av['xyz[0]']), color=col, lw=0.9, label=lab)
        ax.set_xlim(0, t1 - t0)
        ax.set_ylabel('roll rate (deg/s)')
        ax.margins(y=0.3)
        ax.legend(frameon=False, loc='upper right', fontsize=8, ncol=2)
        print(f"  {ctrl}: window {t0:.2f}-{t1:.2f} s, log {t_av[0]:.1f}-{t_av[-1]:.1f} s (timestamps in s)")
    axes[1].set_xlabel('time since start of the metrics window (s)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)
    return None


if __name__ == '__main__':
    miss = {}
    miss['att'] = fig_attitude_ratio()
    miss['eff'] = fig_effort_ratio()
    fig_act_tc_sweep()
    miss['ts'] = fig_timeseries()
    print('\nMissing / skipped:', miss)
    print('Discrepancies > 2 %:', DISCREPANCIES if DISCREPANCIES else 'none')
