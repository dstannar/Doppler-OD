"""
which_TLE: identify which Space-Track TLE corresponds to SAL-E.

This package loads doppler shift profiles and optionally a propagator state with
a configurable weight, filters Space-Track TLEs using SALE.yaml (launch_date,
launch_site), and returns the TLE that minimizes a weighted least-squares cost
(doppler residuals + optional state residuals).

returns the best-matching TLE and scores for all candidates.
"""