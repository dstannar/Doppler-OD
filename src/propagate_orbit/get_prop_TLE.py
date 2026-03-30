"""Numerical propagation: passes, per-pass TLEs, state CSV. Call setup_orekit before importing."""

import csv
from pathlib import Path

from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.orbits import CartesianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.analytical.tle import TLE
from org.orekit.propagation.analytical.tle.generation import FixedPointTleGenerationAlgorithm
from org.orekit.propagation.events import EventsLogger, ExtremumApproachDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent
from org.orekit.propagation.numerical import NumericalPropagator
from org.orekit.time import TimeScalesFactory
from org.orekit.utils import PVCoordinates

from .drag_model import build_drag_force_model as drag
from .j2_model import build_j2_perturbation_model as j2
from .satellite_passes import detect_pass, get_max_elevations, get_pass_intervals


def initial_state_ECEF(Rx, Ry, Rz, Vx, Vy, Vz, epoch, frame, inertial_frame, muE, mass):
    rv_ecef = PVCoordinates(Vector3D(Rx, Ry, Rz), Vector3D(Vx, Vy, Vz))
    rv_eci = frame.getTransformTo(inertial_frame, epoch).transformPVCoordinates(rv_ecef)
    orbit = CartesianOrbit(rv_eci, inertial_frame, epoch, muE)
    return SpacecraftState(orbit, mass)


def get_state(ephemeris, start_date, end_date, fixed_frame, state_csv_path, step_size_sec):
    """Write ECEF state samples to CSV (one row per step_size_sec)."""
    state_csv = Path(state_csv_path)
    utc = TimeScalesFactory.getUTC()

    with state_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["Date (UTC)", "Rx (m)", "Ry (m)", "Rz (m)", "Vx (m/s)", "Vy (m/s)", "Vz (m/s)"]
        )
        t = start_date

        while t.compareTo(end_date) <= 0:
            state = ephemeris.propagate(t)
            pos = state.getPVCoordinates(fixed_frame).getPosition()
            vel = state.getPVCoordinates(fixed_frame).getVelocity()
            writer.writerow(
                [
                    t.toString(utc)[:23],
                    pos.getX(),
                    pos.getY(),
                    pos.getZ(),
                    vel.getX(),
                    vel.getY(),
                    vel.getZ(),
                ]
            )
            t = t.shiftedBy(step_size_sec)

    return state_csv


def get_TLEs(
    position,
    velocity,
    epoch,
    inertial_frame,
    fixed_frame,
    muE,
    gs_name,
    gs_lat,
    gs_long,
    gs_alt,
    gs_min_elev,
    days,
    mass,
    area,
    cd,
    space_weather_file,
    csv_path,
    tle_path,
    state_path,
):
    """Returns passes CSV path, TLE file path, states CSV path."""
    utc = TimeScalesFactory.getUTC()

    rx, ry, rz = position[0], position[1], position[2]
    vx, vy, vz = velocity[0], velocity[1], velocity[2]

    state0 = initial_state_ECEF(rx, ry, rz, vx, vy, vz, epoch, fixed_frame, inertial_frame, muE, mass)

    step_size = 5.0
    integrator = ClassicalRungeKuttaIntegrator(step_size)
    prop = NumericalPropagator(integrator)
    prop.setOrbitType(OrbitType.CARTESIAN)
    prop.setInitialState(state0)
    prop.addForceModel(j2(fixed_frame))
    prop.addForceModel(drag(fixed_frame, area, cd, space_weather_file))

    passes, topo = detect_pass(gs_name, gs_lat, gs_long, gs_alt, gs_min_elev, fixed_frame)
    pass_logger = EventsLogger()
    prop.addEventDetector(pass_logger.monitorDetector(passes))

    max_det = ExtremumApproachDetector(topo).withHandler(ContinueOnEvent())
    max_el_logger = EventsLogger()
    prop.addEventDetector(max_el_logger.monitorDetector(max_det))

    eph_gen = prop.getEphemerisGenerator()
    end = epoch.shiftedBy(days * 86400.0)
    prop.propagate(epoch, end)

    ephem = eph_gen.getGeneratedEphemeris()

    intervals = get_pass_intervals(pass_logger)
    max_el_list = get_max_elevations(max_el_logger, intervals, topo, fixed_frame)

    template_line1 = "1 99999U 26001A   26054.50000000  .00000000  00000-0  00000-0 0  9991"
    template_line2 = "2 99999  97.5000  0.0000 0001000   0.0000   0.0000 15.00000000    01"
    template_TLE = TLE(template_line1, template_line2)

    generator = FixedPointTleGenerationAlgorithm()

    pass_rows = []
    for idx, (aos, los) in enumerate(intervals, start=1):
        tle_epoch = aos.shiftedBy(-600.0)
        state_at_epoch = ephem.propagate(tle_epoch)
        tle = generator.generate(state_at_epoch, template_TLE)

        pass_rows.append(
            {
                "index": idx,
                "aos": aos,
                "los": los,
                "max_elevation": max_el_list[idx - 1]["max_el_deg"],
                "az_at_max_elev": max_el_list[idx - 1]["az_at_max_el"],
                "tle_epoch": tle_epoch,
                "line1": tle.getLine1(),
                "line2": tle.getLine2(),
            }
        )

    csv_path = Path(csv_path)
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "Pass #",
                "AOS (UTC)",
                "LOS (UTC)",
                "TLE Epoch (UTC)",
                "Max Elevation(deg)",
                "Azimuth at Max Elevation(deg)",
            ]
        )
        for r in pass_rows:
            writer.writerow(
                [
                    r["index"],
                    r["aos"].toString(utc)[:23],
                    r["los"].toString(utc)[:23],
                    r["tle_epoch"].toString(utc)[:23],
                    f"{r['max_elevation']:.2f}",
                    f"{r['az_at_max_elev']:.2f}",
                ]
            )

    tle_path = Path(tle_path)
    with tle_path.open("w", newline="\n") as fh:
        for r in pass_rows:
            fh.write(r["line1"].rstrip() + "\n")
            fh.write(r["line2"].rstrip() + "\n\n")

    states_csv = get_state(ephem, epoch, end, fixed_frame, state_path, step_size)

    return csv_path, tle_path, states_csv
