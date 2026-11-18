"""Independent second-key (k120) checks of ident_iv.py. Reference 2SLS + own plant, numpy only."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DT = 1.0 / 800.0
G1, C0 = 80.0, 12.0
ICPT = 0.5 * C0   # true intercept of regression of alpha on du in plant()


def lpf_taps(fc=40.0, n=33):
    t = (np.arange(n) - (n - 1) / 2) * DT
    h = np.exp(-0.5 * (t * 2 * np.pi * fc / 2.5) ** 2)
    return h / h.sum()          # symmetric FIR, zero extra phase, group delay (n-1)/2


def plant(seed, G1=G1, c0=C0, amp=0.3, K=1.5, T=60.0, tau=0.03, dstd=25.0, dtau=0.1, noise=0.002):
    """Closed loop: alpha = G1*u_act + c0 + d ; u_cmd = -K*w_meas_filt + z ; returns raw signals."""
    rng = np.random.default_rng(seed)
    n = int(T / DT)
    t = np.arange(n) * DT
    f = np.linspace(2.0, 30.0, 14)
    ph = rng.uniform(0, 2 * np.pi, f.size)
    z = amp * sum(np.sin(2 * np.pi * fi * t + p) for fi, p in zip(f, ph)) / np.sqrt(f.size / 2)
    # OU disturbance
    a = np.exp(-DT / dtau)
    e = rng.standard_normal(n) * dstd * np.sqrt(1 - a * a)
    d = np.zeros(n)
    for i in range(1, n):
        d[i] = a * d[i - 1] + e[i]
    # hover offset trim: controller removes c0 (so du has ~zero mean): u_hover = -c0/G1
    uh = -0.5 * c0 / G1   # trim cancels only half of c0: true regression intercept = c0/2
    w = np.zeros(n); ua = np.zeros(n); u = np.zeros(n); wf = 0.0
    b = DT / (0.004 + DT)
    wm_n = rng.standard_normal(n) * noise
    for i in range(1, n):
        wf += b * (w[i - 1] + wm_n[i - 1] - wf)
        u[i - 1] = -K * wf + z[i - 1]
        ua[i] = ua[i - 1] + DT / tau * (u[i - 1] - ua[i - 1])
        alpha = G1 * (ua[i] + uh) + c0 + d[i]    # du = ua (increment about hover)
        w[i] = w[i - 1] + DT * alpha
    return dict(t=t, z=z, du=ua, w=w + wm_n, d=d, dt=DT, G1=G1, c0=c0)


def build_xy(s, taps_y=None, taps_x=None, delay_x=0):
    """Same filter + same delay on regressor and regressand (central diff has no delay)."""
    ty = lpf_taps() if taps_y is None else taps_y
    tx = lpf_taps() if taps_x is None else taps_x
    w = s["w"]
    acc = np.zeros_like(w); acc[1:-1] = (w[2:] - w[:-2]) / (2 * DT)
    y = np.convolve(acc, ty, mode="same") if ty is not None else acc
    x = np.convolve(s["du"], tx, mode="same") if tx is not None else s["du"]
    z = s["z"].copy()
    if delay_x:
        x = np.roll(x, delay_x)
    return y, x, z


def ref_2sls(y, x, z, lags=range(0, 41), skip=200):
    """Reference 2SLS: y = b0 + b*x ; instruments = lagged z. Returns beta, c, se, F."""
    n = len(y)
    L = list(lags)
    m = max(L) + skip
    idx = np.arange(m, n - skip)
    Z = np.column_stack([np.ones(idx.size)] + [z[idx - l] for l in L])
    Y, X = y[idx], x[idx]
    g, *_ = np.linalg.lstsq(Z, X, rcond=None)
    Xh = Z @ g
    r1 = X - Xh
    rss1 = r1 @ r1
    Xc = X - X.mean()
    tss = Xc @ Xc
    k = len(L)
    F = ((tss - rss1) / k) / (rss1 / (idx.size - k - 1))
    W = np.column_stack([np.ones(idx.size), Xh])
    b, *_ = np.linalg.lstsq(W, Y, rcond=None)
    Wt = np.column_stack([np.ones(idx.size), X])
    res = Y - Wt @ b
    s2 = res @ res / (idx.size - 2)
    # HAC-free classical se (res is serially correlated -> optimistic); use Newey-West below
    A = np.linalg.inv(W.T @ W)
    se_cl = np.sqrt(s2 * A[1, 1])
    # Newey-West
    Wr = W * res[:, None]
    nl = 60
    S = Wr.T @ Wr
    for l in range(1, nl + 1):
        G = Wr[l:].T @ Wr[:-l]
        S += (1 - l / (nl + 1)) * (G + G.T)
    V = A @ S @ A
    return dict(beta=b[1], c=b[0], se=np.sqrt(V[1, 1]), se_cl=se_cl, F=F, n=idx.size)


def ols(y, x, skip=300):
    sl = slice(skip, len(y) - skip)
    A = np.column_stack([np.ones(len(y[sl])), x[sl]])
    return np.linalg.lstsq(A, y[sl], rcond=None)[0]


# ---------------- tests on the reference itself ----------------
def test_ref_unbiased_ols_biased():
    bi, bo = [], []
    for sd in range(4):
        s = plant(sd)
        y, x, z = build_xy(s)
        bi.append(ref_2sls(y, x, z)["beta"]); bo.append(ols(y, x)[1])
    print("ref IV", np.mean(bi), "OLS", np.mean(bo))
    assert abs(np.mean(bi) / G1 - 1) < 0.03
    assert abs(np.mean(bo) / G1 - 1) > abs(np.mean(bi) / G1 - 1)



import ident_iv as I  # noqa: E402
LAGS = list(range(0, 40, 3))   # 14 lags: well-conditioned; 25+ dense lags make pinv/lstsq diverge (test_rank_deficient_lags)
try:
    import pytest
except ImportError:  # plain runner on a host without pytest
    pytest = None


def _cut(a, s=200):
    return a[s:-s]


def _iv(y, x, z, lags=LAGS, **kw):
    return I.iv_effectiveness(_cut(y), _cut(x), _cut(z), lags=lags, **kw)


def _ref(y, x, z):
    return ref_2sls(_cut(y), _cut(x), _cut(z), lags=LAGS, skip=0)


def test_ident_matches_reference():
    for sd in (0, 1):
        s = plant(sd); y, x, z = build_xy(s)
        a, b = _iv(y, x, z), _ref(y, x, z)
        print("seed", sd, "ident", a["beta"][0], a["intercept"], a["se"][0], a["f_first"][0], "| ref", b["beta"], b["c"], b["se_cl"], b["F"])
        assert np.isclose(a["beta"][0], b["beta"], rtol=1e-6)
        assert np.isclose(a["intercept"], b["c"], rtol=1e-6) and abs(a["intercept"] - ICPT) < 4 * b["se"] * 10
        assert np.isclose(a["se_classical"][0], b["se_cl"], rtol=1e-3)
        assert np.isclose(a["f_first"][0], b["F"], rtol=1e-6)


def test_closed_loop_ols_biased_iv_not():
    e_iv, e_ols = [], []
    for sd in range(3):
        s = plant(sd); y, x, z = build_xy(s)
        r = _iv(y, x, z)
        e_iv.append(r["beta"][0] / G1 - 1); e_ols.append(r["ols"]["beta"][0] / G1 - 1)
    print("IV rel err", np.round(e_iv, 3), "OLS rel err", np.round(e_ols, 3))
    assert abs(np.mean(e_iv)) < 0.03 and abs(np.mean(e_ols)) > 0.3


def test_se_calibration_classical_vs_hac():
    zc, zh, ic = [], [], []
    for sd in range(20):
        s = plant(100 + sd); y, x, z = build_xy(s)
        a, b = _iv(y, x, z), _ref(y, x, z)
        zc.append((a["beta"][0] - G1) / a["se"][0]); zh.append((b["beta"] - G1) / b["se"])
        ic.append(a["intercept"] - ICPT)
    print("z-score std classical(ident se)", np.std(zc), "HAC(ref)", np.std(zh), "mean z", np.mean(zc),
          "intercept err mean/std", np.mean(ic), np.std(ic))
    assert abs(np.mean(zh)) < 1.0 and np.std(zh) < 1.6           # HAC se is calibrated
    assert np.std(zc) < 1.3, "ident_iv classical se is over-confident (serially correlated residual)"


def test_mismatch_filter():
    """y filtered with fc=40 Hz taps, x with fc=15 Hz taps (different filter): must be visibly wrong."""
    out = []
    for sd in range(3):
        s = plant(sd)
        y, x, z = build_xy(s, taps_x=lpf_taps(15.0, 65))
        r = _iv(y, x, z)
        out.append((r["beta"][0] / G1 - 1, r["f_first"][0], r["se"][0] / G1))
    print("filter mismatch (relerr, F, se/G1):", np.round(out, 3).tolist())
    assert abs(np.mean([o[0] for o in out])) > 0.05          # visibly wrong
    assert min(o[1] for o in out) > 10                         # ... but NOT flagged: F stays high
    # (K120 M1 fixed S120: HAC se; the mismatch is caught by J, see test_mismatch_is_flagged_by_estimator)


def test_mismatch_delay():
    """regressor delayed 4 samples (5 ms) relative to regressand."""
    out = []
    for sd in range(3):
        s = plant(sd)
        y, x, z = build_xy(s, delay_x=4)
        r = _iv(y, x, z)
        out.append((r["beta"][0] / G1 - 1, r["f_first"][0], r["se"][0] / G1))
    print("delay mismatch (relerr, F, se/G1):", np.round(out, 3).tolist())
    assert abs(np.mean([o[0] for o in out])) > 0.05
    assert min(o[1] for o in out) > 10


def test_mismatch_is_flagged_by_estimator():
    """Spec (iii): Hansen J separates aligned data from a filter or delay mismatch (K120 B1, fixed S120).
    Breaking check: J computed on aligned data must stay well below J on either mismatch."""
    good, bad = [], []
    for sd in range(3):
        s = plant(sd)
        good.append(_iv(*build_xy(s))["j_stat"])
        bad.append(_iv(*build_xy(s, delay_x=4))["j_stat"])
        bad.append(_iv(*build_xy(s, taps_x=lpf_taps(15.0, 65)))["j_stat"])
    print("J aligned", np.round(good, 1).tolist(), "J mismatched", np.round(bad, 1).tolist())
    assert min(bad) > 3 * max(good), (good, bad)


def test_weak_instrument_f_collapses():
    s_ok = plant(0, amp=0.3); s_w = plant(0, amp=1e-4)
    f_ok = _iv(*build_xy(s_ok))["f_first"][0]
    r = _iv(*build_xy(s_w))
    print("F strong", f_ok, "F weak", r["f_first"][0], "beta weak", r["beta"][0], "se weak", r["se"][0], "f_min", r["f_min"])
    assert f_ok > 100 and r["f_first"][0] < 10
    assert r["se"][0] > 0.2 * G1 or abs(r["beta"][0] / G1 - 1) > 0.2   # visibly unreliable


def test_rank_deficient_lags():
    """Dense lags 0..24 of a 14-tone multisine: Z is numerically near-rank-deficient; ident_iv (pinv default
    rcond) and lstsq disagree by ~0.7 % in beta and ~7 % in F (noise directions kept in the first stage)."""
    s = plant(0); y, x, z = build_xy(s)
    a = I.iv_effectiveness(_cut(y), _cut(x), _cut(z), lags=list(range(25)))
    b = ref_2sls(_cut(y), _cut(x), _cut(z), lags=range(25), skip=0)
    print("dense lags: ident beta/F", a["beta"][0], a["f_first"][0], "ref", b["beta"], b["F"])
    assert np.isclose(a["beta"][0], b["beta"], rtol=1e-3), "pinv vs lstsq truncation differ on ill-conditioned Z"


def test_memory_not_n_squared():
    import tracemalloc
    n = 50000
    rng = np.random.default_rng(0)
    z = rng.standard_normal(n); x = z + 0.3 * rng.standard_normal(n); y = 80 * x + rng.standard_normal(n)
    tracemalloc.start()
    I.iv_effectiveness(y, x, z, lags=LAGS)
    peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    print("peak MB", peak / 1e6)
    assert peak < 150e6        # n x n float64 would be 20 GB; n x q is ~16 MB


if __name__ == "__main__":
    import inspect
    for k, v in list(globals().items()):
        if k.startswith("test_") and callable(v):
            print("RUN", k)
            try:
                v(); print("ok", k)
            except AssertionError as e:
                print("FAIL", k, e)
