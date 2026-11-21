"""Per-run scenario overrides for run_scenario.py (--scenario-overrides FILE.json). Pure, no simulator imports.

Merge rule (shallow): every top-level key of the overrides file REPLACES the same key of the selected scenario dict (the value is
taken whole, never merged field by field); keys the scenario lacks are added. The input scenario is not mutated.

Allowed keys (anything else is rejected):
  thrust_sag   {scale}                              available thrust ramps 1 -> scale over the whole scenario window
  motor_fault  {segment, motor | motors, thrust_scale[, reset]} OR a list of them (reset: true = cumulative scale back to 1 first, G5.10)   step at the start of `segment`; several entries
                                                    (e.g. weak motor + saturation) multiply per motor (fault_entries)
  erpm_loss    {motor, start, end}                  total eRPM loss of one motor from segment `start` to segment `end`
               {motor, start, start_offset_s, duration_s}  timed: loss from (start of segment `start` + offset) for duration
                                                    (sim time); the window must fit inside the scenario
  erpm_frozen  {motor, start, start_offset_s, duration_s}  timed (sim time): rpm of one motor bit-identical, no error count
                                                    (SIM_GZ_ERPM_FRZ); same window rule as timed erpm_loss
  wind         {steady, peak, dir_deg}              gust_x parameters (m/s, m/s TOTAL peak, deg from world +x towards +y);
                                                    any subset; needs disturbance == "gust_x" (scenario's or overridden)
  disturbance  "gust_x" | ...                       injector profile name (a scenario without one can get gust_x)
  dist_segment name                                 segment that starts the disturbance profile (default "dist")
Segment names must exist in the merged scenario's `segments`. validate() raises ValueError with a message naming the key.
"""
import copy
import math

ALLOWED = ("thrust_sag", "motor_fault", "erpm_loss", "erpm_frozen", "wind", "disturbance", "dist_segment")
WIND_KEYS = ("steady", "peak", "dir_deg")
N_MOTORS = 4
WIND_PROFILE_S = 13.0  # gust_x up to the end of the gust (2 ramp + 10 hold + 1 gust); its 15 s tail (28 s total) may run past the window


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _seg_names(sc):
    return [n for n, _, _ in sc["segments"]]


def _need_seg(sc, key, name):
    if name not in _seg_names(sc):
        raise ValueError(f"override {key}: segment {name!r} not in scenario segments {_seg_names(sc)}")


def _seg_start(sc, name):
    t = 0.0
    for n, d, _ in sc["segments"]:
        if n == name:
            return t
        t += d
    raise ValueError(f"segment {name!r} not in scenario")


def _total(sc):
    return sum(d for _, d, _ in sc["segments"])


def _check_fault(sc, f):
    _dict_keys("motor_fault", f, ("segment", "motor", "motors", "thrust_scale", "reset"), ("segment", "thrust_scale"))
    if ("motor" in f) == ("motors" in f):
        raise ValueError("override motor_fault: give exactly one of motor / motors")
    if "motors" in f and (not isinstance(f["motors"], list) or not f["motors"] or len(set(f["motors"])) != len(f["motors"])):
        raise ValueError("override motor_fault: motors must be a non-empty list without duplicates")
    for m in (f["motors"] if "motors" in f else [f["motor"]]):
        _motor("motor_fault", m)
    if not _num(f["thrust_scale"]) or not 0.0 < f["thrust_scale"] <= 1.0:
        raise ValueError(f"override motor_fault: thrust_scale {f['thrust_scale']!r} must be in (0, 1]")
    _need_seg(sc, "motor_fault", f["segment"])


def fault_entries(sc):
    """The scenario's motor_fault as a list of dicts ([] without one); a single dict is a one-entry list."""
    mf = sc.get("motor_fault")
    return [] if not mf else (list(mf) if isinstance(mf, list) else [mf])


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
        mf = ov["motor_fault"]
        if isinstance(mf, list) and not mf:
            raise ValueError("override motor_fault: empty list")
        for f in (mf if isinstance(mf, list) else [mf]):
            _check_fault(sc, f)
    if "erpm_loss" in ov:
        e = ov["erpm_loss"]
        timed = isinstance(e, dict) and ("start_offset_s" in e or "duration_s" in e)
        if timed:
            _dict_keys("erpm_loss", e, ("motor", "start", "start_offset_s", "duration_s"),
                       ("motor", "start", "start_offset_s", "duration_s"))
        else:
            _dict_keys("erpm_loss", e, ("motor", "start", "end"), ("motor", "start", "end"))
        _motor("erpm_loss", e["motor"])
        _need_seg(sc, "erpm_loss", e["start"])
        if timed:
            for k in ("start_offset_s", "duration_s"):
                if not _num(e[k]) or e[k] < 0 or (k == "duration_s" and e[k] <= 0):
                    raise ValueError(f"override erpm_loss: {k} {e[k]!r} must be a finite number (offset >= 0, duration > 0)")
            if _seg_start(sc, e["start"]) + e["start_offset_s"] + e["duration_s"] > _total(sc) + 1e-9:
                raise ValueError(f"override erpm_loss: window [{e['start_offset_s']}, +{e['duration_s']}] s after segment "
                                 f"{e['start']!r} ends beyond the scenario end ({_total(sc)} s)")
        else:
            _need_seg(sc, "erpm_loss", e["end"])
            if _seg_names(sc).index(e["start"]) >= _seg_names(sc).index(e["end"]):
                raise ValueError(f"override erpm_loss: start {e['start']!r} must come before end {e['end']!r}")
    if "erpm_frozen" in ov:
        e = ov["erpm_frozen"]
        _dict_keys("erpm_frozen", e, ("motor", "start", "start_offset_s", "duration_s"),
                   ("motor", "start", "start_offset_s", "duration_s"))
        _motor("erpm_frozen", e["motor"])
        _need_seg(sc, "erpm_frozen", e["start"])
        for k in ("start_offset_s", "duration_s"):
            if not _num(e[k]) or e[k] < 0 or (k == "duration_s" and e[k] <= 0):
                raise ValueError(f"override erpm_frozen: {k} {e[k]!r} must be a finite number (offset >= 0, duration > 0)")
        if _seg_start(sc, e["start"]) + e["start_offset_s"] + e["duration_s"] > _total(sc) + 1e-9:
            raise ValueError(f"override erpm_frozen: window [{e['start_offset_s']}, +{e['duration_s']}] s after segment "
                             f"{e['start']!r} ends beyond the scenario end ({_total(sc)} s)")
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
    if "wind" in ov and sc.get("disturbance") == "gust_x" and sc.get("dist_segment", "dist") in _seg_names(sc):
        if _seg_start(sc, sc.get("dist_segment", "dist")) + WIND_PROFILE_S > _total(sc) + 1e-9:
            raise ValueError(f"override wind: the first {WIND_PROFILE_S} s (ramp, hold, gust) of the gust_x profile from segment {sc.get('dist_segment', 'dist')!r} "
                             f"does not fit in the scenario window ({_total(sc)} s)")
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
