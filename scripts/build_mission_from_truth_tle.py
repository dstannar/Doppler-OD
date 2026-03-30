"""
Build a slightly perturbed initial state in a mission YAML from a Space-Track cohort TLE.

Requires SPACETRACK_USERNAME / SPACETRACK_PASSWORD for get_candidate_tles.
"""

import re

import numpy as np
import yaml

from src.paths import repo_root
from src.setup import setup_orekit

MISSION = "GeoScan5.yaml"
NORAD_ID = 64891

setup_orekit(MISSION)

from configs.config import load_configs
from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.time import TimeScalesFactory
from org.orekit.utils import IERSConventions

from src.helpers.state_from_TLE import state_from_TLE
from src.which_TLE.get_TLEs import get_candidate_tles


def _teme_to_ecef(pos_teme_m, vel_teme_mps, epoch_utc: str, ecef_frame):
    from org.hipparchus.geometry.euclidean.threed import Vector3D
    from org.orekit.frames import FramesFactory
    from org.orekit.time import AbsoluteDate, TimeScalesFactory
    from org.orekit.utils import PVCoordinates

    utc = TimeScalesFactory.getUTC()
    absolute_date = AbsoluteDate(epoch_utc.replace("Z", ""), utc)
    teme = FramesFactory.getTEME()
    pv_teme = PVCoordinates(
        Vector3D(float(pos_teme_m[0]), float(pos_teme_m[1]), float(pos_teme_m[2])),
        Vector3D(float(vel_teme_mps[0]), float(vel_teme_mps[1]), float(vel_teme_mps[2])),
    )
    transform = teme.getTransformTo(ecef_frame, absolute_date)
    pv_ecef = transform.transformPVCoordinates(pv_teme)
    p = pv_ecef.getPosition()
    v = pv_ecef.getVelocity()
    return (
        np.array([p.getX(), p.getY(), p.getZ()], dtype=float),
        np.array([v.getX(), v.getY(), v.getZ()], dtype=float),
    )


def main():
    mission_path = repo_root() / "configs" / MISSION
    if not mission_path.exists():
        raise FileNotFoundError(f"Mission YAML not found: {mission_path}")

    cfg = load_configs(MISSION)

    tles = get_candidate_tles(cfg)
    truth_tle = next((t for t in tles if int(t.getSatelliteNumber()) == int(NORAD_ID)), None)
    if truth_tle is None:
        available = sorted({int(t.getSatelliteNumber()) for t in tles})
        raise RuntimeError(
            f"NORAD ID {NORAD_ID} not found in Space-Track cohort for "
            f"LAUNCH_DATE={cfg.launch_date}, SITE={cfg.launch_site}. "
            f"Available NORAD IDs in cohort: {available[:50]}"
            + (" (truncated)" if len(available) > 50 else "")
        )

    utc = TimeScalesFactory.getUTC()
    truth_epoch = truth_tle.getDate()
    truth_epoch_components = truth_epoch.getComponents(utc)
    truth_date = truth_epoch_components.getDate()
    truth_time = truth_epoch_components.getTime()
    year = truth_date.getYear()
    month = truth_date.getMonth()
    day = truth_date.getDay()
    hour = truth_time.getHour()
    minute = truth_time.getMinute()
    second = truth_time.getSecond()

    epoch_utc_str = truth_epoch.toString(utc)
    if not epoch_utc_str.endswith("Z"):
        epoch_utc_str = epoch_utc_str + "Z"

    pos_teme, vel_teme = state_from_TLE(truth_tle, epoch_utc_str)

    ecef_frame = FramesFactory.getITRF(ITRFVersion.ITRF_2020, IERSConventions.IERS_2010, False)

    pos_ecef, vel_ecef = _teme_to_ecef(pos_teme, vel_teme, epoch_utc_str, ecef_frame)

    rng = np.random.default_rng(16)
    dr = rng.normal(0.0, 2000, size=3)
    dv = rng.normal(0.0, 1, size=3)
    pos_pert = pos_ecef + dr
    vel_pert = vel_ecef + dv

    def _inline_vec(xs):
        return "[" + ", ".join(f"{float(x)}" for x in xs) + "]"

    new_pos = _inline_vec(pos_pert.tolist())
    new_vel = _inline_vec(vel_pert.tolist())

    original_text = mission_path.read_text(encoding="utf-8")

    def _replace_top_level_value(text: str, key: str, new_value_inline: str) -> tuple[str, bool]:
        pat_inline = re.compile(
            rf"^(?P<indent>\s*){re.escape(key)}:\s*(?P<val>.*?)(?P<comment>\s+#.*)?\s*$",
            re.MULTILINE,
        )
        m = pat_inline.search(text)
        if m:
            indent = m.group("indent") or ""
            comment = m.group("comment") or ""
            line = f"{indent}{key}: {new_value_inline}{comment}"
            return text[: m.start()] + line + text[m.end() :], True

        pat_block = re.compile(
            rf"^(?P<indent>\s*){re.escape(key)}:\s*\n(?P<body>(?:^(?P=indent)\s+.*\n)+)",
            re.MULTILINE,
        )
        m = pat_block.search(text + "\n")
        if not m:
            return text, False
        indent = m.group("indent") or ""
        repl = f"{indent}{key}: {new_value_inline}\n"
        new_text = (text + "\n")[: m.start()] + repl + (text + "\n")[m.end() :]
        return new_text.rstrip("\n"), True

    updated_text, ok_pos = _replace_top_level_value(original_text, "position_m", new_pos)
    updated_text, ok_vel = _replace_top_level_value(updated_text, "velocity_mps", new_vel)

    epoch_expr = f"AbsoluteDate({year}, {month}, {day}, {hour}, {minute}, {second},utc)"
    updated_text, ok_epoch = _replace_top_level_value(updated_text, "epoch", epoch_expr)
    updated_text, ok_epoch_utc = _replace_top_level_value(updated_text, "epoch_utc", f'\"{epoch_utc_str}\"')

    if ok_pos and ok_vel and ok_epoch and ok_epoch_utc:
        mission_path.write_text(updated_text, encoding="utf-8")
    else:
        doc = yaml.safe_load(original_text)
        if not isinstance(doc, dict):
            raise RuntimeError(f"Mission YAML root must be a mapping, got {type(doc).__name__}")
        doc["position_m"] = [float(x) for x in pos_pert.tolist()]
        doc["velocity_mps"] = [float(x) for x in vel_pert.tolist()]
        doc["epoch"] = epoch_expr
        doc["epoch_utc"] = epoch_utc_str

        dumped = yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)
        dumped, _ = _replace_top_level_value(dumped, "position_m", new_pos)
        dumped, _ = _replace_top_level_value(dumped, "velocity_mps", new_vel)
        dumped, _ = _replace_top_level_value(dumped, "epoch", epoch_expr)
        dumped, _ = _replace_top_level_value(dumped, "epoch_utc", f'\"{epoch_utc_str}\"')
        mission_path.write_text(dumped, encoding="utf-8")


if __name__ == "__main__":
    main()
