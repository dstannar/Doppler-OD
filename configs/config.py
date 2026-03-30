"""Mission YAML + stations.yaml -> one namespace for the rest of the code."""

from pathlib import Path
from types import SimpleNamespace

import re
import yaml

from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import IERSConventions

from src.paths import repo_root


def load_configs(mission_config: str) -> SimpleNamespace:
    root = repo_root()
    configs_dir = root / "configs"

    with open(configs_dir / mission_config, encoding="utf-8") as f:
        mission = yaml.safe_load(f) or {}

    with open(configs_dir / "stations.yaml", encoding="utf-8") as f:
        stations_data = yaml.safe_load(f) or {}

    def _require(value, name: str):
        if value is None:
            raise ValueError(f"Missing required config value: {name}")
        return value

    def _require_number(value, name: str):
        _require(value, name)
        if not isinstance(value, (int, float)):
            raise ValueError(f"Config value {name} must be numeric, got {type(value).__name__}")
        return float(value)

    required_mission_keys = [
        "launch_date",
        "launch_site",
        "frequency_hz",
        "position_m",
        "velocity_mps",
        "area_m2",
        "cd",
        "mass_kg",
    ]
    for k in required_mission_keys:
        _require(mission.get(k), f"{mission_config}:{k}")

    stations = {
        name: SimpleNamespace(
            lat_deg=_require_number(s.get("lat_deg"), f"stations.{name}.lat_deg"),
            lon_deg=_require_number(s.get("lon_deg"), f"stations.{name}.lon_deg"),
            alt_m=_require_number(s.get("alt_m"), f"stations.{name}.alt_m"),
            min_elevation_deg=_require_number(
                s.get("min_elevation_deg"), f"stations.{name}.min_elevation_deg"
            ),
        )
        for name, s in _require(stations_data.get("stations"), "stations.yaml:stations").items()
    }

    def _abs_path_str(p):
        if p is None:
            return None
        return str((root / str(p)).resolve())

    ecef_frame_cfg = mission.get("ecef_frame")
    inertial_frame_cfg = mission.get("inertial_frame")
    epoch = mission.get("epoch")

    def _parse_inertial_frame(v):
        if not isinstance(v, str) or not v.strip():
            return FramesFactory.getEME2000()
        s = v.strip()
        if "getEME2000" in s or s.upper() == "EME2000":
            return FramesFactory.getEME2000()
        if "getGCRF" in s or s.upper() == "GCRF":
            return FramesFactory.getGCRF()
        if "getICRF" in s or s.upper() == "ICRF":
            return FramesFactory.getICRF()
        return FramesFactory.getEME2000()

    def _parse_ecef_frame(v):
        default_version = ITRFVersion.ITRF_2020
        default_conventions = IERSConventions.IERS_2010
        default_simple_eop = False

        if not isinstance(v, str) or not v.strip():
            return FramesFactory.getITRF(default_version, default_conventions, default_simple_eop)

        s = v.strip()

        if re.fullmatch(r"ITRF_\d{4}", s, flags=re.IGNORECASE):
            name = s.upper()
            version = getattr(ITRFVersion, name, default_version)
            return FramesFactory.getITRF(version, default_conventions, default_simple_eop)

        m_ver = re.search(r"ITRFVersion\.(ITRF_\d{4})", s)
        m_conv = re.search(r"IERSConventions\.(IERS_\d{4})", s)
        m_simple = re.search(r",(?:\s*)(True|False)(?:\s*)\)\s*$", s)

        version = getattr(ITRFVersion, m_ver.group(1)) if m_ver else default_version
        conventions = getattr(IERSConventions, m_conv.group(1)) if m_conv else default_conventions
        simple_eop = (m_simple.group(1) == "True") if m_simple else default_simple_eop

        return FramesFactory.getITRF(version, conventions, simple_eop)

    inertial_frame = _parse_inertial_frame(inertial_frame_cfg)
    ecef_frame = _parse_ecef_frame(ecef_frame_cfg)

    epoch_utc = mission.get("epoch_utc")
    if isinstance(epoch_utc, str) and epoch_utc:
        epoch = AbsoluteDate(epoch_utc.replace("Z", ""), TimeScalesFactory.getUTC())

    return SimpleNamespace(
        launch_date=mission["launch_date"],
        launch_site=mission["launch_site"],
        norad_id=mission.get("NORAD_ID"),
        frequency_hz=mission["frequency_hz"],
        orekit_data_path=_abs_path_str(mission.get("orekit_data_path")),
        doppler_data_dir=_abs_path_str(mission.get("doppler_data_dir")),
        space_weather_file=_abs_path_str(mission.get("space_weather_file")),
        cache_dir=_abs_path_str(mission.get("cache_dir", "TLE-Cache")),
        epoch_utc=mission.get("epoch_utc"),
        epoch=epoch,
        ecef_frame=ecef_frame,
        inertial_frame=inertial_frame,
        position_m=mission["position_m"],
        velocity_mps=mission["velocity_mps"],
        area_m2=mission["area_m2"],
        cd=mission["cd"],
        mass_kg=mission["mass_kg"],
        stations=stations,
    )
