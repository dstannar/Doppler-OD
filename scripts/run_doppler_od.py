"""Run Doppler batch least-squares orbit determination (Orekit BatchLSEstimator)."""

from src.setup import setup_orekit

MISSION = "SALE.yaml"
SIGMA_RANGE_RATE_MPS = 1.0
MAX_ITERATIONS = 25

setup_orekit(MISSION)

from configs.config import load_configs
from src.doppler_OD.solve_od import solve_od


def main():
    cfg = load_configs(MISSION)
    result = solve_od(
        cfg,
        sigma_range_rate_mps=SIGMA_RANGE_RATE_MPS,
        max_iterations=MAX_ITERATIONS,
    )

    rs = result["refined_state"]
    diag = result["diagnostics"]
    cov = result["covariance_6x6"]

    print(f"Mission: {MISSION}")
    print(f"Iterations: {diag['iterations']}  evaluations: {diag['evaluations']}")
    if diag.get("cost") is not None:
        print(f"Cost: {diag['cost']:.6g}")
    if diag.get("residual_rms_mps") is not None:
        print(f"Residual RMS: {diag['residual_rms_mps']:.6g} m/s")

    print("Refined state (ECEF frame at config epoch):")
    print(f"  position_m:  {rs['position_m']}")
    print(f"  velocity_mps: {rs['velocity_mps']}")
    if cov is not None:
        print(f"Covariance (6x6) shape: {cov.shape}")
    else:
        print("Covariance (6x6): unavailable")


if __name__ == "__main__":
    main()
