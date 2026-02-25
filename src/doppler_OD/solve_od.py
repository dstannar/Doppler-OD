"""
Orbit determination end-to-end using Orekit's BatchLSEstimator.

- Take initial state from config (or propagate_orbit).
- Build Orekit range-rate measurements from doppler data (measurement_model).
- Run Orekit's BatchLSEstimator (batch_ls_OD); Orekit handles STM, partials,
  and iteration.
- Return refined state at reference epoch, covariance, and diagnostics
  (residuals, cost, iteration count) from Orekit.
"""


def solve_od(config=None):
    """
    Run Doppler orbit determination end-to-end and return refined state and diagnostics.

    Steps: load config (if None), get measurements and ground stations from
    measurement_model, build propagator from propagate_orbit, run batch_ls_OD,
    extract refined state and covariance.

    Parameters
    ----------
    config : SimpleNamespace or None
        Mission and station config; if None, load via load_configs().

    Returns
    -------
    result : dict or simple object
        At least:
        - refined_state : position_m, velocity_mps at reference epoch
        - covariance : 6x6 array or None
        - diagnostics : dict with e.g. iterations, evaluations, cost,
          optional residuals from batch_ls_OD.get_residuals
    """