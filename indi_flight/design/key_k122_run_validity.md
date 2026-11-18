# K122 review: run_validity.py + g3_run.finalize (code vs spec)

Tests: 23 passed (test_run_validity, test_g3_run).

BLOCKING
1. run_validity.py:14,58-64 - alias CA_R_W_MAX -> MC_INDI_W_MAX (run_scenario.py:826) is not handled. A requested CA_R_W_MAX
   is "missing in log" (or compared to a value the runner never set) -> false void of every run requesting it, and
   the translated MC_INDI_W_MAX value is never verified. Spec lists it explicitly. Fix: map name -> MC_INDI_W_MAX.
2. (low likelihood: main writes g3_params.txt at :310 before flying) g3_run.py:251-253 - ulog present but g3_params.txt absent returns None (unvalidated): outcome stays "ok" with no
   controller check at all. Should call check_run with {} (controller/topic checks need no params) or void.
3. g3_run.py:263 / run_validity.py:82 - exceptions outside the ulog load are not caught. float(pos_req) on a non-numeric
   MC_INDI_POS_EN (already flagged at :56) raises ValueError, and read_params (g3_run.py:47-50) can raise; either
   propagates out of finalize before g3_done.json is written, so the outcome is lost (run retried or campaign dies).
   Wrap check_validity in try/except -> void with problem text, or at least write the marker.

MINOR
4. run_validity.py:59 - MC_RATE_CTL_TYPE skipped whenever absent, even if its requested value contradicts the controller
   (e.g. requested 0 with controller indi + MC_INDI_EN=1 passes). Check want==1 <=> controller indi.
5. run_validity.py:26-32,71 - rate is the median dt over the whole topic, taking data_list's first instance (not
   necessarily multi_id 0). An indi topic alive for a few seconds of a long flight (controller dropped out) passes
   at >=0.8 x rate. Add a coverage check (n >= ~0.8 x rate x flight duration).
6. run_validity.py:18 - inf==inf gives nan compare -> flagged as mismatch (false void); NaN correctly mismatches.
7. run_validity.py:41-47 - pyulog file_corruption / partially parsed log is accepted; check ulog.file_corruption.
8. run_validity.py:90 - pid branch ignores MC_INDI_POS_EN / indi_pos_status; a pid run with pos module active passes.
9. g3_run.py:266 - "incomplete" runs with a ulog are not validated (by spec), but a void stores no g3_outcome change
   for them; fine. Void on "aborted" hides the abort cause only partly: status["error"] is skipped for void (:268),
   so error/watchdog/metrics_status are lost. Copy them before relabelling.

Checked OK: empty topic (n==0) not counted present; string requested values coerced via float; NaN want/got flagged;
missing ulog unchanged (None); void gets g3_done.json and g3_outcome in run.json; unreadable ulog fails closed.
