#!/usr/bin/env python3
"""Self-test for indi_flight/bench/derive_g1.py.

Run: python3 indi_flight/bench/tests/test_derive_g1.py
"""
import math
import os
import sys
import tempfile

import numpy as np

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(BENCH, '..', '..'))
sys.path.insert(0, BENCH)
import derive_g1 as d  # noqa: E402

AIRFRAME = os.path.join(REPO, 'ROMFS', 'px4fmu_common', 'init.d-posix', 'airframes', '4040_gz_quad5in')

# CA_* lines of 4040_gz_quad5in
SYM = {
    'CA_ROTOR_COUNT': '4',
    'CA_ROTOR0_PX': '0.0795', 'CA_ROTOR0_PY': '0.0795', 'CA_ROTOR0_KM': '0.01267',
    'CA_ROTOR1_PX': '-0.0795', 'CA_ROTOR1_PY': '-0.0795', 'CA_ROTOR1_KM': '0.01267',
    'CA_ROTOR2_PX': '0.0795', 'CA_ROTOR2_PY': '-0.0795', 'CA_ROTOR2_KM': '-0.01267',
    'CA_ROTOR3_PX': '-0.0795', 'CA_ROTOR3_PY': '0.0795', 'CA_ROTOR3_KM': '-0.01267',
}
MASS, IXX, IZZ, HOVER = 0.61, 1.396e-3, 2.50e-3, 0.137
IYY = 1.396e-3 * 1.122 / 1.022


def close(name, got, want, tol_rel):
    ok = abs(got - want) <= tol_rel * abs(want)
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {got:.6g}, want {want:.6g} (tol {tol_rel:g} rel)")
    assert ok, name


def test_parse():
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as fh:
        fh.write('CA_ROTOR_COUNT 4\nparam set CA_ROTOR0_PX 0.1\n'
                 'param set-default CA_ROTOR0_PY 0.2\n# comment\nTHR_MDL_FAC 1\n')
    try:
        p = d.read_params(path, {})
    finally:
        os.remove(path)
    assert p == {'CA_ROTOR_COUNT': '4', 'CA_ROTOR0_PX': '0.1', 'CA_ROTOR0_PY': '0.2'}, p
    print('PASS parse: NAME VALUE, param set, param set-default, comments, non-CA ignored')


def test_airframe_matches_sym():
    if not os.path.exists(AIRFRAME):
        print(f'SKIP airframe cross-check: {AIRFRAME} not found')
        return
    p = d.read_params(AIRFRAME, {})
    for k, v in SYM.items():
        assert abs(float(p[k]) - float(v)) < 1e-12, (k, p[k], v)
    print('PASS airframe CA_* lines match the symmetric quad used in this test')


def test_symmetric_quad():
    res = d.derive(SYM, MASS, IXX, IXX, IZZ, HOVER)
    G1 = res['G1']
    closed_roll = MASS * 9.81 * 0.0795 / (math.sqrt(2) * HOVER * IXX)
    close('roll G1 vs closed form m g py / (sqrt2 x ixx)', G1[0], closed_roll, 0.01)
    close('roll G1 vs 1759', G1[0], 1759.0, 0.01)

    expected_yaw = 4 * 0.01267 * (MASS * 9.81 / (4 * HOVER)) / IZZ
    close('yaw G1 vs 4 km (m g / (4 x_hover)) / izz', G1[2], expected_yaw, 0.01)
    close('yaw G1 vs 222', G1[2], 222.0, 0.01)

    res_p = d.derive(SYM, MASS, IXX, IYY, IZZ, HOVER)
    close('pitch G1 = roll x ixx/iyy (iyy = 1.396e-3*1.122/1.022)', res_p['G1'][1], G1[0] * IXX / IYY, 1e-6)
    res_eq = d.derive(SYM, MASS, IXX, IXX, IZZ, HOVER)
    close('pitch G1 = roll when iyy = ixx and |px| = |py|', res_eq['G1'][1], G1[0], 1e-6)

    Mn = res['Mn']
    assert np.allclose(np.abs(Mn[:, 0]), 1 / math.sqrt(2), atol=1e-4), Mn[:, 0]
    assert np.allclose(Mn[:, 0], np.array([-1, 1, 1, -1]) / math.sqrt(2), atol=1e-4), Mn[:, 0]
    assert np.allclose(Mn[:, 2], [1, 1, -1, -1], atol=1e-6), Mn[:, 2]
    print('PASS normalised columns: roll [-,+,+,-]/sqrt2, yaw [1,1,-1,-1]')


def test_nonsymmetric_px_scaled():
    """Scale every PX by 2. Roll rows stay orthogonal, so pinv pitch column halves; PX4 divides it by the
    shared roll/pitch scale = max(roll, pitch), which is unchanged, so the physical pitch G1 is unchanged
    (it does not double). Flagged in the report."""
    base = d.derive(SYM, MASS, IXX, IYY, IZZ, HOVER)
    sym2 = dict(SYM)
    for i in range(4):
        sym2[f'CA_ROTOR{i}_PX'] = str(2 * float(SYM[f'CA_ROTOR{i}_PX']))
    scaled = d.derive(sym2, MASS, IXX, IYY, IZZ, HOVER)

    close('roll G1 unchanged when PX doubled', scaled['G1'][0], base['G1'][0], 1e-9)
    close('pitch G1 unchanged when PX doubled (shared scale)', scaled['G1'][1], base['G1'][1], 1e-6)
    assert np.allclose(scaled['Mn'][:, 1], 0.5 * base['Mn'][:, 1], atol=1e-9), scaled['Mn'][:, 1]
    assert abs(scaled['scale'][0] - base['scale'][0]) < 1e-9 and scaled['scale'][0] == scaled['scale'][1]
    print('FLAG non-symmetric: PX doubled gives pitch G1 ratio 1.0, not 2.0. PX4 normalisation uses the shared '
          'roll/pitch scale, so the pitch column halves and the torque per unit command is unchanged.')


def main():
    test_parse()
    test_airframe_matches_sym()
    test_symmetric_quad()
    test_nonsymmetric_px_scaled()
    print('ALL PASS')


if __name__ == '__main__':
    main()
