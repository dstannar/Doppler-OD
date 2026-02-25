"""
Run Orekit's batch least-squares estimator for orbit determination.

- accept an Orekit propagator builder (same physics as propagate_orbit:
  gravity, drag, etc.) and the list of Orekit measurements (range-rate from
  measurement_model).
- Configure Orekit's BatchLSEstimator with that propagator and measurements.
  Orekit performs the batch LS: state transition matrix, design matrix,
  normal equations, and iteration (e.g. Levenberg-Marquardt).
- Call estimate(); retrieve refined orbital parameters, optional covariance,
  and diagnostics (iterations, residuals) from Orekit. Return state at epoch
  and any requested diagnostics in a form usable by solve_od.
"""


def run_batch_ls(propagator_builder, measurements, optimizer=None, max_iterations=None, max_evaluations=None):
    """
    Run Orekit BatchLSEstimator and return the estimation result.

    Parameters
    ----------
    propagator_builder : Orekit PropagatorBuilder
        Builder that produces propagators with same physics as propagate_orbit (J2, drag).
    measurements : list of Orekit ObservedMeasurement
        Range-rate measurements from measurement_model.build_range_rate_measurements.
    optimizer : Orekit LeastSquaresOptimizer
        e.g. LevenbergMarquardtOptimizer
    max_iterations : int, optional
        Max LS iterations; use Orekit default if None.
    max_evaluations : int, optional
        Max cost evaluations; use Orekit default if None.

    Returns
    -------
    result
        Orekit estimator result object from estimate(), used by
        get_refined_state_and_covariance and get_residuals.
    """


def get_refined_state_and_covariance(estimator_result, epoch):
    """
    Extract refined 6D state and 6x6 covariance at reference epoch from estimator result.

    Parameters
    ----------
    estimator_result : result from run_batch_ls
        Return value of BatchLSEstimator.estimate()
    epoch : Orekit AbsoluteDate or ISO str
        Epoch at which to report state (typically the OD reference epoch).

    Returns
    -------
    state : dict or array
        Position (m) and velocity (m/s) in the propagator frame, e.g.
        {"position_m": [x,y,z], "velocity_mps": [vx,vy,vz]} or (6,) array.
    covariance_6x6 : ndarray or None
        covariance matrix
    """


def get_residuals(estimator_result):
    """
    Return post-fit residuals for diagnostics and plotting.

    Parameters
    ----------
    estimator_result : result from run_batch_ls
        Return value of BatchLSEstimator.estimate()

    Returns
    -------
    list of (time, observed, predicted, residual)
        Per-measurement: time (AbsoluteDate or str), observed range rate (m/s),
        predicted range rate (m/s), residual (m/s)
    """
