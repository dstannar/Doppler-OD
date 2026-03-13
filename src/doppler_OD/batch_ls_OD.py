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

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Initialize Orekit before importing Java package bindings.
try:
    from src.setup import setup_orekit
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from src.setup import setup_orekit

setup_orekit()

import orekit

# Orekit imports (Java classes via JCC)
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.estimation.leastsquares import BatchLSEstimator
from org.hipparchus.optim.nonlinear.vector.leastsquares import LevenbergMarquardtOptimizer


def _as_absolutedate(epoch: Union[AbsoluteDate, str]) -> AbsoluteDate:
    """
    Convert an AbsoluteDate or ISO str to AbsoluteDate (UTC).

    This keeps get_refined_state_and_covariance flexible because solve_od often
    passes epoch around as either an Orekit AbsoluteDate or an ISO timestamp.
    """
    if isinstance(epoch, AbsoluteDate):
        return epoch
    if not isinstance(epoch, str):
        raise TypeError(f"epoch must be AbsoluteDate or str, got {type(epoch)}")
    utc = TimeScalesFactory.getUTC()
    return AbsoluteDate(epoch, utc)


def _realmatrix_to_numpy(m) -> np.ndarray:
    """Convert Hipparchus RealMatrix to numpy array."""
    r = m.getRowDimension()
    c = m.getColumnDimension()
    out = np.empty((r, c), dtype=float)
    for i in range(r):
        for j in range(c):
            out[i, j] = float(m.getEntry(i, j))
    return out


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
    # Default optimizer: Levenberg-Marquardt (common OD choice)
    if optimizer is None:
        optimizer = LevenbergMarquardtOptimizer()

    # Configure Orekit's BatchLSEstimator with that propagator and measurements.
    # Orekit performs the batch LS: state transition matrix, design matrix,
    # normal equations, and iteration (e.g. Levenberg-Marquardt).
    estimator = BatchLSEstimator(optimizer, propagator_builder)

    # Optional stopping/tuning parameters
    if max_iterations is not None:
        estimator.setMaxIterations(int(max_iterations))
    if max_evaluations is not None:
        estimator.setMaxEvaluations(int(max_evaluations))

    # Add all measurements (e.g., range-rate) to the estimator
    if measurements is None or len(measurements) == 0:
        raise ValueError("measurements must be a non-empty list of ObservedMeasurement")
    for m in measurements:
        estimator.addMeasurement(m)

    # Call estimate(); retrieve refined orbital parameters, optional covariance,
    # and diagnostics (iterations, residuals) from Orekit.
    #
    # Note: Orekit's BatchLSEstimator.estimate() returns an array of Propagator,
    # one per estimated satellite, already configured with the estimated parameters.
    propagators = list(estimator.estimate())

    # Return the estimator output plus diagnostics in a form usable by solve_od.
    # Keeping the estimator itself is handy because getPhysicalCovariances()
    # and getLastEstimations() are methods on BatchLSEstimator.
    return {
        "estimator": estimator,
        "propagators": propagators,
        "iterations": int(estimator.getIterationsCount()),
        "evaluations": int(estimator.getEvaluationsCount()),
        "optimum": estimator.getOptimum(),  # Hipparchus least-squares optimum (optional advanced diagnostics)
    }


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
    date = _as_absolutedate(epoch)

    # Most use-cases here are single-spacecraft OD; for multi-sat, pick index.
    propagators = estimator_result["propagators"]
    if len(propagators) == 0:
        raise ValueError("No propagators returned by estimate(); check your builder/measurements.")

    prop = propagators[0]
    state_at_epoch = prop.propagate(date)
    pv = state_at_epoch.getPVCoordinates()

    pos = pv.getPosition()
    vel = pv.getVelocity()

    state = {
        "position_m": [float(pos.getX()), float(pos.getY()), float(pos.getZ())],
        "velocity_mps": [float(vel.getX()), float(vel.getY()), float(vel.getZ())],
    }

    # Optional covariance: Orekit can compute the physical covariance matrix.
    # Important: this covariance is for ALL estimated parameters (orbit + any
    # selected propagation/measurement parameters). If you estimate only the
    # 6 orbital parameters, the leading 6x6 block is typically what you want.
    estimator = estimator_result["estimator"]
    covariance_6x6 = None
    try:
        cov_all = estimator.getPhysicalCovariances(1.0e-20)
        cov_all_np = _realmatrix_to_numpy(cov_all)

        if cov_all_np.shape[0] >= 6 and cov_all_np.shape[1] >= 6:
            covariance_6x6 = cov_all_np[:6, :6].copy()
    except Exception:
        covariance_6x6 = None

    return state, covariance_6x6


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
    estimator = estimator_result["estimator"]

    # getLastEstimations() gives a Map<ObservedMeasurement, EstimatedMeasurement>
    # with observed and estimated values for the last iteration.
    last = estimator.getLastEstimations()

    out = []

    it = last.values().iterator()
    while it.hasNext():
        est_meas = it.next()

        t = est_meas.getDate()
        observed = est_meas.getObservedValue()
        predicted = est_meas.getEstimatedValue()

        # Your measurement set is described as range-rate, which is typically 1D.
        if len(observed) != 1 or len(predicted) != 1:
            raise ValueError(
                f"Expected 1D (range-rate) measurement, got observed dim={len(observed)}, predicted dim={len(predicted)}"
            )

        obs0 = float(observed[0])
        pred0 = float(predicted[0])
        resid0 = obs0 - pred0

        out.append((t, obs0, pred0, resid0))

    # Sort by time for convenience in plotting
    out.sort(key=lambda row: row[0].durationFrom(AbsoluteDate.J2000_EPOCH))
    return out
