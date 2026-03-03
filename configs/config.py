"""
Load and expose mission and station configuration.

- Load SALE.yaml (configs/SALE.yaml) and
  expose launch_date, launch_site, doppler_data_dir, orekit_data_path,
  space_weather_file, and any other fields needed by which_TLE.
- Load stations.yaml and expose stations with lat_deg, lon_deg, alt_m, min_elevation_deg.
- Provide a single place for config paths and parsed structures so the rest of
  the library does not duplicate YAML loading.
"""

from pathlib import Path
from types import SimpleNamespace

import yaml


def _repo_root() -> Path:
    """Repo root (parent of configs/)."""
    return Path(__file__).resolve().parent.parent


def load_configs() -> SimpleNamespace:
    """
    Load SALE.yaml and stations.yaml; return a namespace with all values as attributes.

    Paths (orekit_data_path, doppler_data_dir, space_weather_file) are resolved
    relative to the repo root. stations is a dict[str, SimpleNamespace] with
    lat_deg, lon_deg, alt_m, min_elevation_deg per station.

    Example:
        cfg = load_configs()
        cfg.launch_date
        cfg.orekit_data_path  # Path
        cfg.stations["Marconi"].lat_deg
    """
    root = _repo_root()
    configs_dir = root / "configs"

    with open(configs_dir / "SALE.yaml", encoding="utf-8") as f:
        sale = yaml.safe_load(f)

    with open(configs_dir / "stations.yaml", encoding="utf-8") as f:
        stations_data = yaml.safe_load(f)

    # Resolve path fields relative to repo root
    orekit_data_path = (root / sale["orekit_data_path"]).resolve()
    doppler_data_dir = (root / sale["doppler_data_dir"]).resolve()
    space_weather_file = (root / sale["space_weather_file"]).resolve()

    stations = {
        name: SimpleNamespace(
            lat_deg=s["lat_deg"],
            lon_deg=s["lon_deg"],
            alt_m=s["alt_m"],
            min_elevation_deg=s["min_elevation_deg"],
        )
        for name, s in stations_data["stations"].items()
    }

    return SimpleNamespace(
        # SALE mission / propagator
        launch_date=sale["launch_date"],
        launch_site=sale["launch_site"],
        frequency_hz=sale["frequency_hz"],
        doppler_data_dir=doppler_data_dir,
        orekit_data_path=orekit_data_path,
        space_weather_file=space_weather_file,
        epoch_utc=sale["epoch_utc"],
        frame=sale["frame"],
        position_m=sale["position_m"],
        velocity_mps=sale["velocity_mps"],
        area_m2=sale["area_m2"],
        cd=sale["cd"],
        mass_kg=sale["mass_kg"],
        # Stations (dict of SimpleNamespace)
        stations=stations,
    )
