"""
orbit determination end-to-end using Orekit's BatchLSEstimator.

- Set initial orbit/state from config or caller (e.g. from SALE.yaml or from
  which_TLE best-matching TLE). Build the Orekit propagator (or propagator
  builder) with the same physics as propagate_orbit.
- Build Orekit range-rate measurements from doppler data (measurement_model).
- Run Orekit's BatchLSEstimator (batch_ls); Orekit handles STM, partials, and
  iteration.
- Return refined state at reference epoch, covariance, and
  diagnostics (residuals, cost, iteration count) from Orekit.
"""
