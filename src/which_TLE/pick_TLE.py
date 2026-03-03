"""
pick_TLE.py
Figure out which TLE belongs to us.

- Load config (SALE + stations).
- Load doppler profiles from the configured directory (or accept doppler_records).
- Obtain candidate TLEs (get_TLEs.get_candidate_tles).
- For each candidate TLE: predict doppler (doppler_from_TLE.predict_doppler),
  optionally state at state epoch (state_from_TLE), then combined cost (batch_ls_TLE.combined_cost).
- Return the TLE with minimum cost and ranked list/scores for diagnostics.
"""


def load_doppler_profiles(cfg=None):
    """
    Load Doppler CSV(s) from doppler_data_dir and return flat doppler_records.

    Uses parse_doppler_data.load_doppler_records. For use with match_tle when
    callers do not already have doppler_records.

    Parameters
    ----------
    cfg : SimpleNamespace, optional
        Mission config from load_configs(); if None, load_configs() is called.

    Returns
    -------
    list of dict or structured array
        Flat list of records: time_utc, station_id, doppler_hz (optional: sigma_hz).
    """
    ...


def match_tle(doppler_records, state=None, state_weight=0.0, cfg=None):
    """
    Find the Space-Track TLE that best matches doppler (and optionally state).

    Load config if cfg is None. Get candidate TLEs via get_candidate_tles(cfg).
    For each TLE: get predicted doppler (predict_doppler), optionally get TLE
    state at state epoch (state_from_TLE), compute combined_cost. Return best
    TLE and ranked list (or full scores) for diagnostics.

    Parameters
    ----------
    doppler_records : list of dict or structured array
        Flat list: each item time_utc, station_id, doppler_hz (optional: sigma_hz).
    state : dict, optional
        Optional propagator state: epoch, position_m, velocity_mps (in propagator
        frame). If provided, state_from_TLE(tle, state["epoch"]) is compared.
    state_weight : float
        Weight for state term in combined cost; 0.0 means doppler-only.
    cfg : SimpleNamespace, optional
        Mission config; if None, load_configs() is called (for stations, frame,
        frequency_hz, etc.).

    Returns
    -------
    best_tle
        The TLE with minimum combined cost.
    ranked : list of (tle, cost)
        All candidates sorted by cost ascending, for diagnostics.
    """
    ...