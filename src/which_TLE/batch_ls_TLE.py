"""
batch_ls_TLE.py
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


def cost_doppler(doppler_records, predicted_doppler_hz, sigma_hz=None):
    """
    Sum of squared Doppler residuals (observed − predicted).

    Parameters
    ----------
    doppler_records : list of dict or structured array
        Each item: time_utc, station_id, doppler_hz (optional: sigma_hz).
    predicted_doppler_hz : array-like
        Predicted Doppler in Hz, same length and order as doppler_records.
    sigma_hz : float or array-like, optional
        Per-observation or scalar sigma (Hz) for weighted LS; if None, unweighted.

    Returns
    -------
    float
        Sum of squared residuals
    """
    ...


def cost_state(state_obs, state_tle, weights=None):
    """
    Sum of squared position and velocity residuals between two 6D states.

    Parameters
    ----------
    state_obs : dict or array-like
        Observed state: position_m (3), velocity_mps (3) or (6,) array.
    state_tle : dict or array-like
        TLE state at same epoch; same format as state_obs.
    weights : array-like, optional
        Optional weights (e.g. 1/sigma^2) for position and velocity terms.

    Returns
    -------
    float
        Sum of squared residuals (optionally weighted).
    """
    ...


def combined_cost(
    doppler_records,
    predicted_doppler_hz,
    state_obs=None,
    state_tle=None,
    state_weight=0.0,
    sigma_hz=None,
):
    """
    Combined cost = cost_doppler + state_weight * cost_state.

    If state_obs or state_tle is None, the state term is omitted.

    Parameters
    ----------
    doppler_records : list of dict or structured array
        Each item: time_utc, station_id, doppler_hz.
    predicted_doppler_hz : array-like
        Predicted Doppler in Hz, same length and order as doppler_records.
    state_obs : dict or array-like, optional
        Propagator state (position_m, velocity_mps or (6,) at epoch).
    state_tle : dict or array-like, optional
        TLE state at same epoch (e.g. from state_from_TLE).
    state_weight : float
        Weight for state cost term; 0.0 means doppler-only.
    sigma_hz : float or array-like, optional
        Per-observation or scalar sigma (Hz) for cost_doppler.

    Returns
    -------
    float
        Combined cost.
    """
    ...
