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


def load_configs() -> SimpleNamespace:
    """
    Load SALE.yaml and stations.yaml; return a namespace with all values as attributes.

    Paths (orekit_data_path, doppler_data_dir, space_weather_file) are resolved
    relative to the repo root. stations is a dict[str, SimpleNamespace] with
    lat_deg, lon_deg, alt_m, min_elevation_deg per station.

    Example:
        cfg = load_configs()
        cfg.launch_date
        cfg.orekit_data_path
        cfg.stations["Marconi"].lat_deg
    """
    root = Path(__file__).resolve().parent.parent
    configs_dir = root / "configs"

    with open(configs_dir / "SALE.yaml", encoding="utf-8") as f:
        sale = yaml.safe_load(f)

    with open(configs_dir / "stations.yaml", encoding="utf-8") as f:
        stations_data = yaml.safe_load(f)

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
        orekit_data_path = sale["orekit_data_path"],
        doppler_data_dir = sale["doppler_data_dir"],
        space_weather_file =sale["space_weather_file"],
        cache_dir = sale["cache_dir"],
        epoch_utc=sale["epoch_utc"],
        epoch = sale["epoch"],
        ecef_frame=sale["ecef_frame"],
        inertial_frame=sale["inertial_frame"],
        position_m=sale["position_m"],
        velocity_mps=sale["velocity_mps"],
        area_m2=sale["area_m2"],
        cd=sale["cd"],
        mass_kg=sale["mass_kg"],
        # Stations dict
        stations=stations,
    )
