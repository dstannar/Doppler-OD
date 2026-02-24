"""
doppler_OD: orbit determination from one-way doppler using Orekit batch least squares.

This package refines an initial orbit estimate using doppler observations and
the physical propagator (same model as propagate_orbit). Orekit performs the
batch least-squares estimation: state transition matrix, measurement partials,
normal equations, and iteration. doppler_OD loads config and doppler data,
builds Orekit range-rate measurements and the propagator, and runs Orekit's
BatchLSEstimator.
"""
