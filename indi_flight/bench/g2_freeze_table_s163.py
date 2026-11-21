#!/usr/bin/env python3
"""S163: tabulate G2 freeze cells. Rate cells (g2_freeze_s160/*_s[0-9]): primary margins.txt (last JSON line),
key2.md (second_key_m3a_s100 variant A), holes.txt OVERALL, accepted bins. Outer cells (g2_outer_freeze_s163/*_margins.json)."""
import json, re, sys, glob, os
R = 'indi_flight/results'
def last_json(p):
    for line in reversed(open(p).read().splitlines()):
        if line.startswith('{'): return json.loads(line)
def overall(p):
    if not os.path.exists(p): return 'n/a'
    m = re.search(r'OVERALL (\w+)', open(p).read()); return m.group(1) if m else '?'
print('| rate cell | PM deg | GM dB | DM ms | key2 PM / GM | dPM / dGM | bins | holes | verdict |\n|---|---|---|---|---|---|---|---|---|')
for d in sorted(glob.glob(f'{R}/g2_freeze_s160/*_s[0-9]')):
    n = os.path.basename(d)
    if not ('yaw' in n or '_mo_' in n): continue
    j = last_json(f'{d}/margins.txt'); txt = open(f'{d}/margins.txt').read()
    b = re.search(r'n_bins (\d+) accepted (\d+)', txt); bins = f'{b.group(2)}/{b.group(1)}' if b else '?'
    k = re.search(r'- PM ([\d.]+) deg, crossover [\d.]+ Hz, GM ([\d.]+) dB', open(f'{d}/key2.md').read())
    kp, kg = float(k.group(1)), float(k.group(2))
    pm, gm, dm = j['pm_deg'], j['gm_db'], j['dm_s'] * 1e3
    ok = pm >= 45 and gm >= 6 and abs(kp - pm) <= 3 and abs(kg - gm) <= 1 and overall(f'{d}/holes.txt') == 'PASS'
    print(f'| {n} | {pm:.1f} | {gm:.1f} | {dm:.1f} | {kp:.1f} / {kg:.1f} | {kp-pm:+.1f} / {kg-gm:+.2f} | {bins} | {overall(d+"/holes.txt")} | {"PASS" if ok else "CHECK"} |')
print('\n| outer cell | PM deg | GM dB | DM s | f_c Hz | Ms | holes | margins PASS |\n|---|---|---|---|---|---|---|---|')
for p in sorted(glob.glob(f'{R}/g2_outer_freeze_s163/*_margins.json')):
    n = os.path.basename(p)[:-13]; m = json.load(open(p))['margins']
    gm = m.get('gm_db'); fc = m['crossings'][0]['f_c'] if m.get('crossings') else float('nan')
    ok = m['pm_deg'] >= 45 and (gm is None or gm >= 6)
    gms = 'none in band' if gm is None else f'{gm:.1f}'
    print(f"| {n} | {m['pm_deg']:.1f} | {gms} | {m['dm_s']:.3f} | {fc:.2f} | {m.get('Ms', float('nan')):.2f} | {overall(p.replace('_margins.json','_holes.txt'))} | {'PASS' if ok else 'FAIL'} |")
