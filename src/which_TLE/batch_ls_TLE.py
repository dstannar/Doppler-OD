"""
batch_ls_TLE.py
Weighted least-squares cost utilities for TLE matching.
"""

import numpy as np

def cost_doppler(doppler_records: np.ndarray, predicted_doppler_hz: np.ndarray):
    """
    Sum of squared Doppler residuals (observed − predicted).

    Parameters
    ----------
    doppler_records
        Each item: time_utc, station_id, doppler_hz
        Can be a list of dicts or a numpy structured array.
    predicted_doppler_hz
        Predicted Doppler in Hz, same length and order as doppler_records.

    Returns
    -------
    float
        Sum of squared residuals.
    """
    observed = doppler_records[:, 2] # doppler_hz
    predicted = predicted_doppler_hz

    if observed.shape != predicted.shape:
        raise ValueError(
            f"Observed and predicted Doppler lengths differ: "
            f"{observed.shape} vs {predicted.shape}"
        )

    residuals = observed - predicted

    cost = float(np.dot(residuals, residuals))

    return cost




def cost_state(state_pred: np.ndarray, state_tle: np.ndarray):
    """
    Sum of squared position and velocity residuals between two 6D states.

    Parameters
    ----------
    state_obs
        Observed state: position_m (3), velocity_mps (3) or (6,) array.
    state_tle
        TLE state at same epoch; same format as ``state_obs``.
    weights
        Optional scalar or per-component weights (e.g. 1/sigma^2) applied to the
        squared residuals.

    Returns
    -------
    float
        Sum of squared residuals
    """
    pos_pred = state_pred[0:3]
    vel_pred = state_pred[3:6]
    pos_tle = state_tle[0:3]
    vel_tle = state_tle[3:6]

    delta_pos = pos_pred - pos_tle
    delta_vel = vel_pred - vel_tle
    delta = np.concatenate([delta_pos, delta_vel])
    cost = float(np.dot(delta, delta))

    return cost


def combined_cost(doppler_records: np.ndarray, predicted_doppler_hz: np.ndarray, state_obs = None, state_tle = None, state_weight = 1.0):
    """
    Combined Doppler and state least-squares cost.

    The total cost is::

        cost = cost_doppler(...) + state_weight * cost_state(...)

    If ``state_obs`` or ``state_tle`` is ``None``, the state term is omitted.

    Parameters
    ----------
    doppler_records
        Each item: time_utc, station_id, doppler_hz.
    predicted_doppler_hz
        Predicted Doppler in Hz, same length and order as ``doppler_records``.
    state_obs
        Propagator state (position_m, velocity_mps or length-6 array) at epoch.
    state_tle
        TLE state at same epoch (e.g. from ``state_from_TLE``); same format
        as ``state_obs``.
    state_weight
        Weight for state cost term; 0.0 means doppler-only.
    sigma_hz
        Per-observation or scalar sigma (Hz) passed through to ``cost_doppler``.

    Returns
    -------
    float
        Combined cost.
    """
    cost = cost_doppler(doppler_records, predicted_doppler_hz)

    if state_obs is not None and state_tle is not None:
        cost += state_weight * cost_state(state_obs, state_tle)

    return float(cost)
