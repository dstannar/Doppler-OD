"""
pick_TLE.py
figure out which TLE belongs to us

- Load config (SALE + stations).
- Load doppler profiles from the configured directory
- Obtain candidate TLEs (call get_TLEs.py)
- For each candidate TLE: compute predicted doppler (doppler_from_TLE.py), optionally
  compute state at state epoch (state_from_TLE.py), then compute combined cost (compute_LS_cost.py).
- Return the TLE with minimum cost as the best match and return a
  ranked list or full scores for all candidates for diagnostics.
"""