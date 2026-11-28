"""Shared matplotlib style and path helpers for the report figures."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))        # indi_flight/
OUTDIR = os.path.join(ROOT, "report", "pdf", "figures")

INDIBLUE = "#1F4E79"    # INDI
INDIGREY = "#595959"    # PID reference
INDIORANGE = "#C55A11"  # thresholds and limits
INDILIGHT = "#DCE6F2"   # bands
INDIGREEN = "#548235"   # pass
INDIRED = "#A50021"     # fail

FULL = 6.0  # inch
HALF = 2.9

_names = {f.name for f in font_manager.fontManager.ttflist}
SERIF = "Libertinus Serif" if "Libertinus Serif" in _names else None


def apply():
    rc = {
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#444444", "axes.linewidth": 0.6,
        "axes.grid": True, "grid.color": "#E3E3E3", "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "lines.linewidth": 1.1, "lines.markersize": 4,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    }
    if SERIF:
        rc["font.serif"] = [SERIF, "DejaVu Serif"]
    else:
        rc["font.serif"] = ["CMU Serif", "Computer Modern Roman", "DejaVu Serif"]
    plt.rcParams.update(rc)


def path(rel):
    """Absolute path of a file given relative to indi_flight/."""
    return os.path.join(ROOT, rel)


def read(rel):
    with open(path(rel)) as fh:
        return fh.read()


def save(fig, name):
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, name + ".pdf")
    fig.savefig(out)
    plt.close(fig)
    print("wrote", out)
    return out


def panel_label(ax, s):
    ax.text(-0.02, 1.02, s, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")


apply()
