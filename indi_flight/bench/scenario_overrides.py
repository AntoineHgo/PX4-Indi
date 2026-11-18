"""Per-run scenario overrides for run_scenario.py (--scenario-overrides FILE.json). Pure, no simulator imports.

Merge rule (shallow): every top-level key of the overrides file REPLACES the same key of the selected scenario dict (the value is
taken whole, never merged field by field); keys the scenario lacks are added. The input scenario is not mutated.

Allowed keys (anything else is rejected):
  thrust_sag   {scale}                              available thrust ramps 1 -> scale over the whole scenario window
  motor_fault  {segment, motor | motors, thrust_scale}   step at the start of `segment`
  erpm_loss    {motor, start, end}                  total eRPM loss of one motor from segment `start` to segment `end`
  wind         {steady, peak, dir_deg}              gust_x parameters (m/s, m/s TOTAL peak, deg from world +x towards +y);
                                                    any subset; needs disturbance == "gust_x" (scenario's or overridden)
  disturbance  "gust_x" | ...                       injector profile name (a scenario without one can get gust_x)
  dist_segment name                                 segment that starts the disturbance profile (default "dist")
Segment names must exist in the merged scenario's `segments`. validate() raises ValueError with a message naming the key.
"""
import copy
import math

ALLOWED = ("thrust_sag", "motor_fault", "erpm_loss", "wind", "disturbance", "dist_segment")
WIND_KEYS = ("steady", "peak", "dir_deg")
N_MOTORS = 4


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _seg_names(sc):
    return [n for n, _, _ in sc["segments"]]


def _need_seg(sc, key, name):
    if name not in _seg_names(sc):
        raise ValueError(f"override {key}: segment {name!r} not in scenario segments {_seg_names(sc)}")


def _motor(key, m):
    if not isinstance(m, int) or isinstance(m, bool) or not 0 <= m < N_MOTORS:
        raise ValueError(f"override {key}: motor index {m!r} must be an int in 0..{N_MOTORS - 1}")


def _dict_keys(key, v, allowed, required=()):
    if not isinstance(v, dict):
        raise ValueError(f"override {key}: expected an object, got {type(v).__name__}")
    bad = sorted(set(v) - set(allowed))
    if bad:
        raise ValueError(f"override {key}: unknown field(s) {bad}, allowed {sorted(allowed)}")
    miss = [k for k in required if k not in v]
    if miss:
        raise ValueError(f"override {key}: missing field(s) {miss}")


def validate(sc, ov):
    """sc = merged scenario, ov = the overrides dict (only its keys are checked, against the merged scenario)."""
    for k in ov:
        if k not in ALLOWED:
            raise ValueError(f"unknown override key {k!r}, allowed {list(ALLOWED)}")
    if "thrust_sag" in ov:
        _dict_keys("thrust_sag", ov["thrust_sag"], ("scale",), ("scale",))
        s = ov["thrust_sag"]["scale"]
        if not _num(s) or not 0.0 < s <= 1.0:
            raise ValueError(f"override thrust_sag: scale {s!r} must be a number in (0, 1]")
    if "motor_fault" in ov:
        f = ov["motor_fault"]
        _dict_keys("motor_fault", f, ("segment", "motor", "motors", "thrust_scale"), ("segment", "thrust_scale"))
        if ("motor" in f) == ("motors" in f):
            raise ValueError("override motor_fault: give exactly one of motor / motors")
        for m in (f["motors"] if "motors" in f else [f["motor"]]):
            _motor("motor_fault", m)
        if "motors" in f and (not isinstance(f["motors"], list) or not f["motors"] or len(set(f["motors"])) != len(f["motors"])):
            raise ValueError("override motor_fault: motors must be a non-empty list without duplicates")
        if not _num(f["thrust_scale"]) or not 0.0 < f["thrust_scale"] <= 1.0:
            raise ValueError(f"override motor_fault: thrust_scale {f['thrust_scale']!r} must be in (0, 1]")
        _need_seg(sc, "motor_fault", f["segment"])
    if "erpm_loss" in ov:
        e = ov["erpm_loss"]
        _dict_keys("erpm_loss", e, ("motor", "start", "end"), ("motor", "start", "end"))
        _motor("erpm_loss", e["motor"])
        _need_seg(sc, "erpm_loss", e["start"])
        _need_seg(sc, "erpm_loss", e["end"])
        if _seg_names(sc).index(e["start"]) >= _seg_names(sc).index(e["end"]):
            raise ValueError(f"override erpm_loss: start {e['start']!r} must come before end {e['end']!r}")
    if "dist_segment" in ov:
        _need_seg(sc, "dist_segment", ov["dist_segment"])
    if "disturbance" in ov and not isinstance(ov["disturbance"], str):
        raise ValueError("override disturbance: expected a profile name")
    if "wind" in ov:
        w = ov["wind"]
        _dict_keys("wind", w, WIND_KEYS)
        if sc.get("disturbance") != "gust_x":
            raise ValueError(f"override wind: needs disturbance 'gust_x', scenario has {sc.get('disturbance')!r} "
                             "(add 'disturbance': 'gust_x' and 'dist_segment' to the overrides)")
        for k, v in w.items():
            if not _num(v):
                raise ValueError(f"override wind: {k} {v!r} is not a finite number")
        if w.get("steady", 3.0) < 0.0:
            raise ValueError("override wind: steady must be >= 0")
        if "peak" in w and w["peak"] < w.get("steady", 3.0):
            raise ValueError(f"override wind: peak {w['peak']} (total) must be >= steady {w.get('steady', 3.0)}")
    if sc.get("disturbance") and sc.get("dist_segment", "dist") not in _seg_names(sc):
        raise ValueError(f"override disturbance: dist_segment {sc.get('dist_segment', 'dist')!r} not in segments {_seg_names(sc)}")


def merge(sc, ov):
    """Shallow-merge ov into a copy of scenario sc, validate, return the merged dict."""
    if not isinstance(ov, dict):
        raise ValueError("overrides file must hold a JSON object")
    out = copy.deepcopy(sc)
    out.update(copy.deepcopy(ov))
    validate(out, ov)
    return out


def wind_flags(sc):
    """Extra disturbance.py arguments of the merged scenario's `wind` dict ([] without one)."""
    w = sc.get("wind") or {}
    flag = {"steady": "--wind-steady", "peak": "--wind-peak", "dir_deg": "--wind-dir"}
    return [x for k in WIND_KEYS if k in w for x in (flag[k], repr(float(w[k])))]
