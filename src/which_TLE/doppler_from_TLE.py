"""
doppler_from_TLE.py
Compute predicted doppler from a TLE at ground stations

- Given a TLE and a list of ground stations (from config), propagate the TLE
  with Orekit over the observation times from the recorded doppler profile.
- Compute the line-of-sight range rate at each time and station and convert to
  doppler shift in Hz (same sign convention as the observed profile: positive =
  approaching).
- Return predicted doppler time series per station so compute_LS_cost.py can form
  observed-minus-predicted residuals.
"""
