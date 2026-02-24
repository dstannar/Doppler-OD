"""
batch_ls.py
Weighted least-squares cost for TLE matching.

- cost_doppler: for each observation time and station, residual = observed
  doppler − TLE-predicted doppler to give sum of squared residuals
- cost_state (optional): at the state epoch, position and velocity residuals
  between the user-supplied state (from propagate_orbit) and the TLE state to give 
  sum of squared residuals.
- combined cost: cost = cost_doppler + state_weight * cost_state, with a
  modifiable state_weight so callers can tune how much the propagator state
  influences the match versus doppler alone depending on how confident we are in propagation
"""
