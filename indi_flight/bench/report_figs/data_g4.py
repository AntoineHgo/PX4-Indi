"""G4 effort table (R20, C20, R4) per noise profile from the committed score file."""
import re

from style import path, read

G4 = "results/freeze10_s193/G4_SCORES.md"


def load():
    """dict run -> dict(r20, r20_lim, c20, c20_lim, r4, r4_lim), values as printed (fz10 columns)."""
    txt = read(G4)
    sec = txt.split("## Effort")[1].split("## Noise")[0]
    out = {}
    num = r"([0-9.]+) \(([0-9.]+)\) P"
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or not re.match(r"(hover|cruise)_(quiet|typ|harsh)_s\d$", cells[0]):
            continue
        r20, c20, r4 = (re.match(num, cells[i]) for i in (1, 3, 5))
        out[cells[0]] = dict(r20=float(r20[1]), r20_lim=float(r20[2]), c20=float(c20[1]), c20_lim=float(c20[2]),
                             r4=float(r4[1]), r4_lim=float(r4[2]))
    return out
