"""Loaders for the G2 margin results (committed files only)."""
import glob
import json
import os
import re

from style import path, read

G2O = "results/freeze10_s193/g2o"
ATT = "results/freeze10_s193/g2s/ax2_r400_s1_margins.json"
RATE = "results/freeze10_s193/g2s/roll800_fwdef_s2/margins.txt"


def open_read(fn):
    with open(fn) as fh:
        return fh.read()


def outer_cells():
    """24 outer-loop cells: dict name -> dict(pt, ax, rate, seed, pm, gm, dm_ms, f, L_abs)."""
    cells = {}
    for fn in sorted(glob.glob(path(G2O + "/pt*_margins.json"))):
        name = os.path.basename(fn)[: -len("_margins.json")]
        m = re.match(r"pt(\d)_ax(\d)_r(\d+)_s(\d)", name)
        d = json.loads(open_read(fn))
        mg = d["margins"]
        gms = [c["gm_db"] for c in mg["phase_crossings"]]
        cells[name] = dict(pt=int(m[1]), ax=int(m[2]), rate=int(m[3]), seed=int(m[4]),
                           pm=mg["pm_deg"], gm=min(gms) if gms else None,
                           dm_ms=mg["dm_s"] * 1e3, f=d["f"], L_abs=d["L_abs"])
    return cells


def att_spot():
    mg = json.loads(read(ATT))["margins"]
    # Q13 A reading: the 4.29 Hz crossing (|L| < 1) is the gain margin; the 0.237 Hz crossing has |L| > 1
    pos = [c["gm_db"] for c in mg["phase_crossings"] if c["gm_db"] > 0]
    return dict(pm=mg["pm_deg"], gm=min(pos), dm_ms=mg["dm_s"] * 1e3, f_c=mg["crossings"][0]["f_c"],
                signed_min_gm=min(c["gm_db"] for c in mg["phase_crossings"]),
                f_gm=[c["f"] for c in mg["phase_crossings"] if c["gm_db"] > 0][0])


def rate_spot():
    txt = read(RATE).splitlines()
    f = json.loads(re.search(r"^f (\[.*\])", "\n".join(txt), re.M)[1])
    mag = json.loads(re.search(r"^\|L\| dB (\[.*\])", "\n".join(txt), re.M)[1])
    arg = json.loads(re.search(r"^arg deg (\[.*\])", "\n".join(txt), re.M)[1])
    mg = json.loads([l for l in txt if l.startswith("{")][0])
    return dict(f=f, mag_db=mag, arg_deg=arg, pm=mg["pm_deg"], dm_ms=mg["dm_s"] * 1e3,
                gm=mg["gm_db"], f_c=mg["crossings"][0]["f_c"], f_gm=mg["phase_crossings"][0]["f"])
