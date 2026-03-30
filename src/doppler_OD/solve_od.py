"""
Orbit determination end-to-end using Orekit's BatchLSEstimator.

- Take initial state from config (or propagate_orbit).
- Build Orekit range-rate measurements from doppler data (measurement_model).
- Run Orekit's BatchLSEstimator (batch_ls_OD); Orekit handles STM, partials,
  and iteration.
- Return refined state at reference epoch, covariance, and diagnostics
  (residuals, cost, iteration count) from Orekit.
"""

from __future__ import annotations

import numpy as np
from org.orekit.attitudes import LofOffset
from org.orekit.frames import LOFType
from org.orekit.orbits import OrbitType, PositionAngle
from org.orekit.propagation.conversion import NumericalPropagatorBuilder
from org.orekit.utils import Constants

from configs.config import load_configs
from src.doppler_OD.batch_ls_OD import get_refined_state_and_covariance, get_residuals, run_batch_ls
from src.doppler_OD.measurement_model import get_measurements
from src.propagate_orbit.drag_model import build_drag_force_model
from src.propagate_orbit.get_prop_TLE import initial_state_ECEF
from src.propagate_orbit.j2_model import build_j2_perturbation_model


def solve_od(
    config=None,
    *,
    mission_yaml: str = "SALE.yaml",
    sigma_range_rate_mps: float = 1.0,
    max_iterations: int = 25,
    max_evaluations: int | None = None,
):
    """
    Run Doppler orbit determination end-to-end and return refined state and diagnostics.

    Steps: load config (if None), get measurements and ground stations from
    measurement_model, build propagator from propagate_orbit, run batch_ls_OD,
    extract refined state and covariance.

    Parameters
    ----------
    config : SimpleNamespace or None
        Mission and station config; if None, load via load_configs(mission_yaml).
    mission_yaml : str
        Used when config is None.
    sigma_range_rate_mps : float
        Range-rate measurement sigma (m/s) for all Doppler points.
    max_iterations, max_evaluations : int, optional
        Passed to BatchLSEstimator.

    Returns
    -------
    result : dict
        - refined_state : position_m, velocity_mps at reference epoch
        - covariance_6x6 : ndarray or None
        - diagnostics : iterations, evaluations, cost, residuals list
    """
    if config is None:
        config = load_configs(mission_yaml)

    if not getattr(config, "doppler_data_dir", None):
        raise ValueError("Mission config must set doppler_data_dir for Doppler OD.")

    _, measurements = get_measurements(
        config.doppler_data_dir,
        config.stations,
        config.ecef_frame,
        float(config.frequency_hz),
        sigma_range_rate_mps,
    )
    if not measurements:
        raise ValueError("No Doppler measurements were built; check doppler_data_dir and CSVs.")

    mu = Constants.WGS84_EARTH_MU
    rx, ry, rz = config.position_m[0], config.position_m[1], config.position_m[2]
    vx, vy, vz = config.velocity_mps[0], config.velocity_mps[1], config.velocity_mps[2]
    state0 = initial_state_ECEF(
        rx,
        ry,
        rz,
        vx,
        vy,
        vz,
        config.epoch,
        config.ecef_frame,
        config.inertial_frame,
        mu,
        float(config.mass_kg),
    )
    orbit = state0.getOrbit()
    attitude = LofOffset(config.inertial_frame, LOFType.LVLH_CCSD)
    builder = NumericalPropagatorBuilder(
        orbit,
        OrbitType.CARTESIAN,
        PositionAngle.TRUE,
        1.0,
        attitude,
        0.001,
        100.0,
        1.0e-9,
    )
    builder.setMass(float(config.mass_kg))
    builder.addForceModel(build_j2_perturbation_model(config.ecef_frame))
    builder.addForceModel(
        build_drag_force_model(
            config.ecef_frame,
            float(config.area_m2),
            float(config.cd),
            config.space_weather_file,
        )
    )

    estimator_result = run_batch_ls(
        builder,
        measurements,
        max_iterations=max_iterations,
        max_evaluations=max_evaluations,
    )

    refined_state, covariance_6x6 = get_refined_state_and_covariance(estimator_result, config.epoch)
    residuals = get_residuals(estimator_result)
    optimum = estimator_result.get("optimum")
    cost = float(optimum.getCost()) if optimum is not None else None

    resid_mps = np.array([float(r[3]) for r in residuals], dtype=float)
    rms = float(np.sqrt(np.mean(resid_mps**2))) if len(resid_mps) else None

    return {
        "refined_state": refined_state,
        "covariance_6x6": covariance_6x6,
        "diagnostics": {
            "iterations": estimator_result["iterations"],
            "evaluations": estimator_result["evaluations"],
            "cost": cost,
            "residuals": residuals,
            "residual_rms_mps": rms,
        },
    }
