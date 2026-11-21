"""Self-test of the Q18 A land-window skip, key 2 (bench/g4_chatter_skip_key2.py). Run: python3 this_file  (exit 0 = pass)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g4_chatter_skip_key2 as S

def test_skip_logic():
    S.BREAK = False
    assert S.self_test()

def test_break_is_caught():
    S.BREAK = True
    try: assert not S.self_test(), "broken skip went undetected"
    finally: S.BREAK = False

if __name__ == "__main__":
    test_skip_logic(); test_break_is_caught(); print("OK (skip passes, broken skip fails as required)")
