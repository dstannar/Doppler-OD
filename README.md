# Doppler-OD

Orbit tools for Cal Poly CubeSat Lab: one-way Doppler analysis and least-squares orbit determination using [Orekit](https://www.orekit.org/) (Java) via Python.

## What’s in the repo

| Area | Role |
|------|------|
| `configs/` | Mission YAML (`SALE.yaml`, `GeoScan5.yaml`, …), station lists, shared constants via `configs/config.py` |
| `SALE-Doppler/` | Doppler CSVs (layout set in mission config `doppler_data_dir`) |
| `orekit-data/` | Orekit ancillary data (frames, time scales, space weather, etc.); path comes from mission `orekit_data_path` |
| `src/propagate_orbit/` | Numerical propagation (J2, drag) and TLE-related helpers |
| `src/doppler_OD/` | Batch LS OD on Doppler (Orekit `BatchLSEstimator`) |
| `src/which_TLE/` | Match Space-Track TLEs to your Doppler; predict Doppler from a TLE |

Space-Track is only used where TLEs are fetched from the API. Follow [Space-Track best practices](https://www.space-track.org/documentation) and avoid unnecessary requests.

## Prerequisites

1. **Python 3.10+** and dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. **Orekit Python bindings** and a JVM — the project imports `orekit`; install them for your OS (not listed in `requirements.txt` today).
3. **Orekit data** on disk at the path in your mission YAML (`orekit_data_path`, default `orekit-data` at repo root).
4. **Space-Track**: set in the environment:
   - `SPACETRACK_USERNAME`
   - `SPACETRACK_PASSWORD`  
   (See `src/which_TLE/get_TLEs.py` for notes.)

## Scripts (from repo root)

| Script | Purpose |
|--------|---------|
| `scripts/run_which_tle.py` | Load Doppler from the mission config, score candidate TLEs, print best NORAD and residuals, optional plot of CSV vs TLE-predicted Doppler. Uses `states.csv` when `consider_states` is enabled (see script constants). |
| `scripts/run_doppler_od.py` | Run batch least-squares OD from configured Doppler and mission setup. |
| `scripts/test_propagation.py` | Compare numerical propagation to SGP4 for a truth TLE (`GeoScan5.yaml` by default). |
| `scripts/build_mission_from_truth_tle.py` | Build/perturb mission YAML initial state from a cohort TLE (Space-Track API). |

Edit the `MISSION = "....yaml"` (and other constants) at the top of each script to match your case.

Propagation outputs such as `states.csv` / `passes.csv` are produced by the propagate/TLE tooling (e.g. `src/propagate_orbit/run_tles.py`), not by `run_which_tle.py` itself — generate those first if your TLE matching expects them.

## Code conventions (short)

- SI units in new code; in code and names use `SALE` (not `SAL-E`).
- Shared constants: `configs/config.py`; Orekit VM and data path: `src/setup.py` (`setup_orekit`).
- Style: type hints on new functions, docstrings where non-obvious, `snake_case` / `PascalCase` for functions vs classes; prefer vectorized NumPy over tight Python loops where it matters.

## Git workflow

Use a feature branch and open a PR to `main` when ready. For Git basics (clone, branch, push), use your usual docs or `git --help`.
