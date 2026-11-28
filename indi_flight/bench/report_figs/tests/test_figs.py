#!/usr/bin/env python3
"""Checks that the numbers loaded by the figure scripts match the numbers printed in the report chapters,
and a smoke run of every figure script.   Run:  python3 indi_flight/bench/report_figs/tests/test_figs.py"""
import importlib
import os
import re
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import style  # noqa: E402

REPORT = os.path.join(style.ROOT, "report")


def _rd(p):
    with open(p) as fh:
        return fh.read()


def chapter(name):
    return _rd(os.path.join(REPORT, name))


CH3 = chapter("03_validation.md")
CH4 = chapter("04_limits.md")


def printed(text, v, nd=None):
    """True if the number v occurs in text as printed (some decimal spellings are tried)."""
    forms = {repr(float(v)), f"{v:g}", f"{v:.1f}", f"{v:.2f}", f"{v:.3f}", f"{v:.4f}"}
    if nd is not None:
        forms = {f"{v:.{nd}f}"}
    return any(re.search(r"(?<![0-9.])" + re.escape(f) + r"(?![0-9])", text) for f in forms)


class TestMargins(unittest.TestCase):
    def test_outer_cells(self):
        import data_g2
        c = data_g2.outer_cells()
        self.assertEqual(len(c), 24)
        pm = min(v["pm"] for v in c.values())
        self.assertAlmostEqual(pm, 49.1, delta=0.05)
        self.assertEqual(min(c, key=lambda k: c[k]["pm"]), "pt0_ax2_r400_s2")
        self.assertIn("49.1 deg", CH3)
        gm_xy = min(v["gm"] for v in c.values() if v["pt"] == 0 and v["ax"] in (1, 2))
        self.assertAlmostEqual(gm_xy, 13.5, delta=0.05)
        self.assertIn("13.5 dB", CH3)
        dm = min(v["dm_ms"] for v in c.values())
        self.assertAlmostEqual(dm, 229, delta=0.5)
        self.assertEqual(min(c, key=lambda k: c[k]["dm_ms"]), "pt1_ax3_r800_s1")
        self.assertIn("229 ms", CH3)
        self.assertGreaterEqual(pm, 45.0)
        # no -180 deg crossing in the band: 4 pt0 z cells + 3 of the 4 pt1 z cells (chapter 2 section 8 says 4/8, see FIGURES.md)
        self.assertEqual(sum(1 for v in c.values() if v["gm"] is None), 7)
        self.assertTrue(all(v["gm"] >= 6 for v in c.values() if v["gm"] is not None))
        # pt1_ax3_r800_s2 primary GM 22.4 dB (chapter table)
        self.assertAlmostEqual(c["pt1_ax3_r800_s2"]["gm"], 22.4, delta=0.05)
        self.assertAlmostEqual(c["pt1_ax1_r800_s1"]["pm"], 71.3, delta=0.05)

    def test_spot_cells(self):
        import data_g2
        r = data_g2.rate_spot()
        self.assertAlmostEqual(r["gm"], 15.7, delta=0.05)
        self.assertAlmostEqual(r["pm"], 46.9, delta=0.05)
        self.assertAlmostEqual(r["dm_ms"], 75.5, delta=0.05)
        self.assertIn("GM 15.7 dB, PM 46.9 deg, DM 75.5 ms", CH3)
        a = data_g2.att_spot()
        self.assertAlmostEqual(a["gm"], 13.7, delta=0.05)
        self.assertAlmostEqual(a["f_gm"], 4.29, delta=0.005)
        self.assertAlmostEqual(a["pm"], 48.0, delta=0.05)
        self.assertAlmostEqual(a["dm_ms"], 93.5, delta=0.05)
        self.assertAlmostEqual(a["signed_min_gm"], -17.31, delta=0.005)
        self.assertIn("GM 13.7 dB at 4.29 Hz, PM 48.0 deg, DM 93.5 ms", CH3)
        self.assertIn("-17.31 dB", CH3)

    def test_bode_table(self):
        import data_g2
        r = data_g2.rate_spot()
        self.assertEqual(len(r["f"]), 18)
        # crossing frequency lies where |L| crosses 0 dB, phase there gives the stated PM
        f, m, p = np.array(r["f"]), np.array(r["mag_db"]), np.array(r["arg_deg"])
        k = np.nonzero(m < 0)[0][0]
        self.assertTrue(f[k - 1] < r["f_c"] < f[k])
        ph_c = np.interp(r["f_c"], f, p)
        self.assertAlmostEqual(180 + ph_c, r["pm"], delta=2.0)


class TestSteps(unittest.TestCase):
    def test_indi_metrics_match_scorer(self):
        import data_steps as ds
        txt = style.read("results/freeze10_s193/steps/step_out.txt")
        for ax in ds.AXES:
            row = [l for l in txt.splitlines() if f"seed1/step_{ax}_indi" in l][0].split("|")
            os_ref, settle_ref = float(row[6]), float(row[7])
            os_, settle = ds.metrics(ds.load("indi", ax))
            self.assertAlmostEqual(os_, os_ref, delta=0.05, msg=ax)
            self.assertAlmostEqual(settle, settle_ref, delta=10.0, msg=ax)  # 5 ms output grid
            self.assertLessEqual(os_, 5.0)
            self.assertLessEqual(settle, ds.LIM[ax][1])
        self.assertIn("0.65 %", CH3)
        self.assertIn("347.5 ms", CH3)

    def test_pid_reference_within_derivation_values(self):
        import data_steps as ds
        self.assertIn("settle max 412 ms", CH3)
        self.assertIn("settle max 1240 ms", CH3)
        for ax, lim in (("roll", 412), ("pitch", 412), ("yaw", 1240)):
            os_, settle = ds.metrics(ds.load("pid", ax))
            self.assertLessEqual(os_, 0.3 + 0.01)
            self.assertLessEqual(settle, lim)

    def test_traces_small(self):
        d = os.path.join(style.ROOT, "results/report_traces")
        tot = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d) if f.endswith(".csv"))
        self.assertLess(tot, 300e3 * 4)  # <300 kB per figure group
        for f in os.listdir(d):
            if f.endswith(".csv"):
                self.assertLess(os.path.getsize(os.path.join(d, f)), 300e3)


class TestCampaign(unittest.TestCase):
    def test_counts(self):
        import collections
        import data_g3
        rows = data_g3.load()
        self.assertEqual(len(rows), 300)
        c = collections.Counter(r["status"] for r in rows)
        scored = c["pass"] + c["fail"]
        self.assertEqual(scored, 297)
        self.assertEqual(c["fail"], 79)
        self.assertEqual(c["loc"], 2)
        self.assertIn("79 of 297", CH3)
        self.assertIn("300/300 flown", CH3)
        self.assertIn("run 245", CH3)
        self.assertIn("run 264", CH3)
        self.assertEqual({r["idx"] for r in rows if r["status"] == "loc"}, {245, 264})
        self.assertEqual(sum(r["item2_any"] for r in rows), 79)
        item3 = sum(r["item3_k1"] for r in rows)
        self.assertAlmostEqual(100 * (scored - item3) / scored, 94.95, delta=0.005)
        self.assertIn("94.95 %", CH3)
        self.assertTrue(all(0.5 <= r["tau"] <= 3.0 for r in rows))
        self.assertTrue(all(0.0 <= r["delay"] <= 10.0 for r in rows))
        self.assertTrue(all(0.7 <= r["mass"] <= 1.3 for r in rows))
        self.assertIn("0.5-3", CH3)
        # draw 264 (run 264): thrust scale 0.351, motor 3 at 0.709, mass 1.3 as in the chapter
        r264 = [r for r in rows if r["idx"] == 264][0]
        self.assertAlmostEqual(r264["mass"], 1.3, places=3)
        self.assertIn("thrust scale 0.351", CH3)


class TestNoise(unittest.TestCase):
    def test_effort(self):
        import data_g4
        d = data_g4.load()
        self.assertEqual(len(d), 18)
        hh = [v for k, v in d.items() if k.startswith("hover_harsh")]
        self.assertAlmostEqual(max(v["r20"] for v in hh), 0.016)
        self.assertAlmostEqual(max(v["c20"] for v in hh), 0.00025)
        self.assertAlmostEqual(max(v["r4"] for v in hh), 0.042)  # s3 0.042, chapter quotes the 0.041 of s1/s2
        self.assertIn("0.016 % / 0.00025 / 0.041 %", CH3)
        self.assertIn("3 / 0.012 / 6", CH3)
        self.assertEqual({(hh[0]["r20_lim"], hh[0]["c20_lim"], hh[0]["r4_lim"])}, {(3.0, 0.012, 6.0)})
        ch = [v for k, v in d.items() if k.startswith("cruise_harsh")]
        self.assertEqual((min(v["r20"] for v in ch), max(v["r20"] for v in ch)), (0.023, 0.024))
        self.assertEqual((min(v["c20"] for v in ch), max(v["c20"] for v in ch)), (0.00065, 0.00067))
        self.assertEqual((min(v["r4"] for v in ch), max(v["r4"] for v in ch)), (0.271, 0.295))
        self.assertIn("0.023-0.024 % / 0.00065-0.00067 / 0.271-0.295 %", CH3)
        self.assertEqual(ch[0]["r20_lim"], 4.5)
        self.assertIn("4.5 / 0.018 / 6", CH3)
        for v in d.values():  # every run passes
            self.assertLess(v["r20"], v["r20_lim"])
            self.assertLess(v["c20"], v["c20_lim"])
            self.assertLess(v["r4"], v["r4_lim"])


class TestModes(unittest.TestCase):
    def test_rows_in_chapter(self):
        import data_g5
        for lab, v, lim, unit, pid in data_g5.ROWS:
            self.assertLessEqual(v, lim, lab)
            self.assertTrue(printed(CH3, v), f"{lab}: worst {v} not in chapter 3")
            self.assertTrue(printed(CH3, lim), f"{lab}: limit {lim} not in chapter 3")
            if pid is not None:
                self.assertTrue(printed(CH3, pid), f"{lab}: PID {pid} not in chapter 3")


class TestLimits(unittest.TestCase):
    def test_draw264_tilt(self):
        import fig_limits
        d = fig_limits.csv("g3_draw264_tilt")
        self.assertGreater(d["tilt_indi_deg"].max(), 60.0)
        self.assertLess(d["tilt_pid_deg"].max(), 60.0)
        self.assertIn("PID flies the same draw without LOC", CH4)
        self.assertIn("tilt max 40 deg", CH3)  # chapter value is from the ground-truth tilt, longer window
        self.assertIn("60 deg", CH4)

    def test_draw3_oscillation(self):
        import fig_limits
        d = fig_limits.csv("g3_draw3_pitch_rate")
        fs = 1 / np.median(np.diff(d["t_s"]))
        peaks = {}
        for k in ("q_indi_dps", "q_pid_dps"):
            x = d[k] - d[k].mean()
            f = np.fft.rfftfreq(len(x), 1 / fs)
            p = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
            m = (f > 1.5) & (f < 3.0)
            peaks[k] = (f[m][p[m].argmax()], p[m].max())
        self.assertAlmostEqual(peaks["q_indi_dps"][0], 2.0, delta=0.25)           # 2 Hz line (chapter: 2.00 Hz)
        self.assertGreater(10 * np.log10(peaks["q_indi_dps"][1] / peaks["q_pid_dps"][1]), 30.0)  # chapter: about 30 dB
        self.assertIn("2.00 Hz", CH3)
        self.assertIn("about 30 dB", CH3)


class TestSmoke(unittest.TestCase):
    def test_every_script_writes_a_pdf(self):
        names = {"fig_g2_margins": "g2_margins", "fig_g2_bode_rate": "g2_bode_rate", "fig_steps": "step_attitude",
                 "fig_g3_campaign": "g3_campaign", "fig_g4_noise": "g4_noise_effort", "fig_g5_modes": "g5_modes",
                 "fig_limits": "limits_failures"}
        for mod, pdf in names.items():
            out = os.path.join(style.OUTDIR, pdf + ".pdf")
            if os.path.exists(out):
                os.remove(out)
            importlib.import_module(mod).main()
            self.assertTrue(os.path.getsize(out) > 5000, pdf)
            with open(out, "rb") as fh:
                self.assertEqual(fh.read(5), b"%PDF-")


if __name__ == "__main__":
    unittest.main(verbosity=2)
