#!/usr/bin/env python3
"""Self-test of g3_item2_split.py: a 2 Hz sine placed only before the cut is flagged pre-cut, not post-cut (both keys).
Needs scipy: indi_project/docker/run.sh -n t -- python3 indi_flight/bench/tests/test_item2_split.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_item2_split  # noqa: E402

sys.exit(0 if g3_item2_split.self_test() else 1)
