import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from g2_plateau_key2_s175 import analyse


def test_clean_crossover():
    # phase passes -180 between 20 and 40 Hz; |L| -20 dB at crossing
    r = analyse([1, 10, 20, 40], [10, -5, -20, -20], [-90, -120, -150, -210])
    assert abs(r['classic'] - 20.0) < 1e-9 and r['plateau'] is None and r['red'] is None


def test_plateau_below_one():
    # bin at -175 deg with -9 dB, true crossing later at -30 dB
    r = analyse([1, 5, 10, 20, 40], [10, -3, -9, -20, -30], [-90, -120, -175, -178, -200])
    assert abs(r['plateau'] - 20.0) < 1e-9 or abs(r['plateau'] - 9.0) < 1e-9
    assert abs(r['plateau'] - 9.0) < 1e-9          # bins at -175 (9 dB) and -178 (20 dB)
    assert r['classic'] > 20 and r['ok'] is True


def test_above_one_near_minus180():
    r = analyse([1, 5, 10, 20], [12, 3, -8, -15], [-100, -172, -150, -160])
    assert abs(r['red'] - 3.0) < 1e-9 and r['ok'] is False
    # a gain-reduction bin is not a plateau bin
    assert r['plateau'] is None


def test_wrap():
    # +170 deg == -190 deg: within 10 of -180
    r = analyse([1, 10, 20], [5, -12, -30], [-100, 170, 100])
    assert abs(r['plateau'] - 12.0) < 1e-9
    assert abs(r['classic'] - 12.0) < 20  # crossing between 1 and 10 exists
    assert r['classic'] is not None


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('ok', n)
