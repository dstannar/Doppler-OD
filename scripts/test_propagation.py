"""
Compare numerical propagation (J2 + drag) to SGP4 from a truth TLE.

IC for the numerical run is ECEF PV from the TLE at element epoch (not YAML state).
"""

import math
from collections import defaultdict
from math import degrees, radians

from src.setup import setup_orekit

MISSION = "GeoScan5.yaml"
# Total span in days, or a list/tuple of 1-based day indices to report (duration = max(indices)).
DAYS = 10.0
STEP_SEC = 60.0
DENOM_FLOOR = 1.0

setup_orekit(MISSION)

from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.bodies import GeodeticPoint, OneAxisEllipsoid
from org.orekit.frames import TopocentricFrame
from org.orekit.orbits import OrbitType
from org.orekit.propagation.analytical.tle import TLEPropagator
from org.orekit.propagation.numerical import NumericalPropagator
from org.orekit.time import TimeScalesFactory
from org.orekit.utils import Constants

from configs.config import load_configs
from src.propagate_orbit.drag_model import build_drag_force_model
from src.propagate_orbit.get_prop_TLE import initial_state_ECEF
from src.propagate_orbit.j2_model import build_j2_perturbation_model
from src.which_TLE.get_TLEs import get_tle_for_norad_id


def _pct_err(pred: float, truth: float, floor: float) -> float:
    d = abs(truth)
    if d < floor:
        d = floor
    return abs(pred - truth) / d * 100.0


def _circular_abs_diff_deg(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _duration_days_and_report_days(days) -> tuple[float, list[int]]:
    if isinstance(days, (list, tuple, range)):
        idx = sorted({int(d) for d in days})
        if not idx or min(idx) < 1:
            raise ValueError("DAYS as a sequence must be non-empty 1-based day indices.")
        return float(max(idx)), idx
    d = float(days)
    if d <= 0:
        raise ValueError("DAYS must be positive.")
    n = int(math.ceil(d))
    return d, list(range(1, n + 1))


def main():
    cfg = load_configs(MISSION)
    if cfg.norad_id is None:
        raise SystemExit(f"Mission {MISSION} must define NORAD_ID for this test.")

    def _build_num_ephemeris(tle_epoch, tle_prop, step_sec: float, duration_sec: float):
        s0 = tle_prop.propagate(tle_epoch)
        pv = s0.getPVCoordinates(cfg.ecef_frame)
        p = pv.getPosition()
        v = pv.getVelocity()
        rx, ry, rz = float(p.getX()), float(p.getY()), float(p.getZ())
        vx, vy, vz = float(v.getX()), float(v.getY()), float(v.getZ())
        mu = Constants.WGS84_EARTH_MU
        state0 = initial_state_ECEF(
            rx,
            ry,
            rz,
            vx,
            vy,
            vz,
            tle_epoch,
            cfg.ecef_frame,
            cfg.inertial_frame,
            mu,
            float(cfg.mass_kg),
        )
        integrator = ClassicalRungeKuttaIntegrator(float(step_sec))
        prop = NumericalPropagator(integrator)
        prop.setOrbitType(OrbitType.CARTESIAN)
        prop.setInitialState(state0)
        prop.addForceModel(build_j2_perturbation_model(cfg.ecef_frame))
        prop.addForceModel(
            build_drag_force_model(
                cfg.ecef_frame,
                float(cfg.area_m2),
                float(cfg.cd),
                cfg.space_weather_file,
            )
        )
        end = tle_epoch.shiftedBy(float(duration_sec))
        eph_gen = prop.getEphemerisGenerator()
        prop.propagate(tle_epoch, end)
        return eph_gen.getGeneratedEphemeris()

    def run_compare(
        truth_tle,
        duration_days: float,
        report_day_indices: list[int],
        sample_step_sec: float,
        denom_floor: float,
    ):
        duration_sec = float(duration_days) * 86400.0
        tle_prop = TLEPropagator.selectExtrapolator(truth_tle)
        tle_epoch = truth_tle.getDate()
        num_eph = _build_num_ephemeris(tle_epoch, tle_prop, sample_step_sec, duration_sec)

        gs = cfg.stations["Marconi"]
        r_earth = Constants.WGS84_EARTH_EQUATORIAL_RADIUS
        flat = Constants.WGS84_EARTH_FLATTENING
        earth = OneAxisEllipsoid(r_earth, flat, cfg.ecef_frame)
        gp = GeodeticPoint(radians(gs.lat_deg), radians(gs.lon_deg), float(gs.alt_m))
        topo = TopocentricFrame(earth, gp, "Marconi")

        n = int(duration_sec / sample_step_sec)
        if n < 0:
            raise ValueError("duration must be non-negative")
        sums = {"Rx": 0.0, "Ry": 0.0, "Rz": 0.0, "Vx": 0.0, "Vy": 0.0, "Vz": 0.0}
        sum_mae_el_by_day: defaultdict[int, float] = defaultdict(float)
        sum_mae_az_by_day: defaultdict[int, float] = defaultdict(float)
        count_by_day: defaultdict[int, int] = defaultdict(int)
        count = 0

        for k in range(n + 1):
            dt_sec = k * sample_step_sec
            t = tle_epoch.shiftedBy(dt_sec)
            day_idx = int(dt_sec // 86400.0) + 1
            ns = num_eph.propagate(t)
            ts = tle_prop.propagate(t)
            npv = ns.getPVCoordinates(cfg.ecef_frame)
            tpv = ts.getPVCoordinates(cfg.ecef_frame)
            npos, nvel = npv.getPosition(), npv.getVelocity()
            tpos, tvel = tpv.getPosition(), tpv.getVelocity()
            sums["Rx"] += _pct_err(float(npos.getX()), float(tpos.getX()), denom_floor)
            sums["Ry"] += _pct_err(float(npos.getY()), float(tpos.getY()), denom_floor)
            sums["Rz"] += _pct_err(float(npos.getZ()), float(tpos.getZ()), denom_floor)
            sums["Vx"] += _pct_err(float(nvel.getX()), float(tvel.getX()), denom_floor)
            sums["Vy"] += _pct_err(float(nvel.getY()), float(tvel.getY()), denom_floor)
            sums["Vz"] += _pct_err(float(nvel.getZ()), float(tvel.getZ()), denom_floor)
            el_num = float(degrees(topo.getElevation(npos, cfg.ecef_frame, t)))
            az_num = float(degrees(topo.getAzimuth(npos, cfg.ecef_frame, t)))
            el_tle = float(degrees(topo.getElevation(tpos, cfg.ecef_frame, t)))
            az_tle = float(degrees(topo.getAzimuth(tpos, cfg.ecef_frame, t)))
            sum_mae_el_by_day[day_idx] += abs(el_num - el_tle)
            sum_mae_az_by_day[day_idx] += _circular_abs_diff_deg(az_num, az_tle)
            count_by_day[day_idx] += 1
            count += 1

        means_pct = {key: sums[key] / count for key in sums}
        mae_el_by_day = {
            d: sum_mae_el_by_day[d] / count_by_day[d]
            for d in report_day_indices
            if d in count_by_day
        }
        mae_az_by_day = {
            d: sum_mae_az_by_day[d] / count_by_day[d]
            for d in report_day_indices
            if d in count_by_day
        }
        return means_pct, tle_epoch, mae_el_by_day, mae_az_by_day

    duration_days, report_days = _duration_days_and_report_days(DAYS)
    truth_tle = get_tle_for_norad_id(int(cfg.norad_id), cache_dir=cfg.cache_dir)
    means, tle_epoch, mae_el_by_day, mae_az_by_day = run_compare(
        truth_tle, duration_days, report_days, STEP_SEC, DENOM_FLOOR
    )

    utc = TimeScalesFactory.getUTC()
    print(f"Mission: {MISSION}  NORAD_ID: {int(cfg.norad_id)}")
    print(f"TLE epoch (UTC): {tle_epoch.toString(utc)[:23]}  span: {duration_days} d  step: {STEP_SEC} s")
    print("Mean absolute percent error vs TLE (ECEF), each component:")
    for k in ("Rx", "Ry", "Rz", "Vx", "Vy", "Vz"):
        print(f"  {k}: {means[k]:.6f} %")
    print("Mean absolute error vs TLE at Marconi (deg), by day from epoch (24 h bins):")
    for d in report_days:
        if d not in mae_el_by_day:
            print(f"  day {d}: (no samples in window)")
            continue
        print(
            f"  day {d}:  elevation MAE {mae_el_by_day[d]:.6f} deg,  "
            f"azimuth MAE {mae_az_by_day[d]:.6f} deg"
        )


if __name__ == "__main__":
    main()
