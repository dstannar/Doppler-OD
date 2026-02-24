"""
orbit determination end-to-end using Orekit's BatchLSEstimator.

- take initial state from propagate_orbit
- Build Orekit range-rate measurements from doppler data (measurement_model).
- Run Orekit's BatchLSEstimator (batch_ls); Orekit handles STM, partials, and
  iteration.
- Return refined state at reference epoch, covariance, and
  diagnostics (residuals, cost, iteration count) from Orekit.
"""
