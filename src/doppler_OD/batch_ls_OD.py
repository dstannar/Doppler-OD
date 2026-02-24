"""
Run Orekit's batch least-squares estimator for orbit determination.

- Build or accept an Orekit propagator builder (same physics as propagate_orbit:
  gravity, drag, etc.) and the list of Orekit measurements (range-rate from
  measurement_model).
- Configure Orekit's BatchLSEstimator with that propagator and measurements.
  Orekit performs the batch LS: state transition matrix, design matrix,
  normal equations, and iteration (e.g. Levenberg-Marquardt).
- Call estimate(); retrieve refined orbital parameters, optional covariance,
  and diagnostics (iterations, residuals) from Orekit. Return state at epoch
  and any requested diagnostics in a form usable by solve_od.
"""
