"""
which_TLE: identify which Space-Track TLE corresponds to SAL-E.

This package loads doppler shift profiles and optionally a propagator state with
a configurable weight, filters Space-Track TLEs using SALE.yaml (launch_date,
launch_site), and returns the TLE that minimizes a weighted least-squares cost
(doppler residuals + optional state residuals).

Public API: match_tle(doppler_profiles, state=None, state_weight=0.0, ...)
returns the best-matching TLE and scores for all candidates.
"""