| log | t0_s | arm_s | r_first | r_arm | pre_min | pre_max | post_absmax | z_reset |
|---|---|---|---|---|---|---|---|---|
| results/a14_s21/r1/flight.ulg | 20.836 | 30.010 | -0.009 | -0.008 | -0.030 | 0.028 | 0.170 | 0 |
| results/a14_s21/r2/flight.ulg | 21.189 | 30.020 | -0.037 | -0.005 | -0.041 | 0.023 | 0.173 | 0 |
| results/a14_s21/r3/flight.ulg | 20.979 | 30.006 | 0.036 | 0.042 | 0.017 | 0.051 | 0.074 | 0 |
    self._file_handle = open(log_file, "rb") #pylint: disable=consider-using-with
                        ^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'results/a14_s21/r4/flight.ulg'
| indi_flight/results/a14_s21/r4/flight.ulg | 30.004 | 30.006 | -2.265 | -2.265 | -2.265 | -2.265 | 2.266 | 0 |
| indi_flight/results/a14_s21/r5/flight.ulg | 30.010 | 30.015 | 0.059 | 0.059 | 0.059 | 0.059 | 0.098 | 0 |
| indi_flight/results/a14_s21/r6/flight.ulg | 30.011 | 30.010 | -0.036 | -0.036 | nan | nan | 0.152 | 0 |
