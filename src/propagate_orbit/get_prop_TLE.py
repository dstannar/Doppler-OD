"""
 Propagate Orbit

 Description: this script will use take the state vector of SAL-E given by SpaceX prelaunch ODM
 and propagate it forward to when we can expect a pass and return it as a TLE. The generated TLE 
 will be given to Satnet as an estimate for where to point Marconi antennas during SAL-E's first passes. 

 Inputs: 
 - state vector (ECEF frame from SpaceX)
 - gs location 
 - time of propagation (1 week)


 Outputs:
 - propagated state in TLE format
 - time of each pass after launch (PST)

"""
from pathlib import Path
import sys


#initialize
import os, sys, string, math
from tempfile import template
import numpy as np
# init orekit
from setup import setup_orekit
setup_orekit()

#import orekit libraries
import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator

from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.utils import IERSConventions
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.utils import PVCoordinates, Constants
from org.orekit.orbits import CartesianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.numerical import NumericalPropagator


#import perturbation functions
from src.propagate_orbit.j2_model import build_j2_perturbation_model as j2
from src.propagate_orbit.drag_model import build_drag_force_model as drag
from src.propagate_orbit.satellite_passes import detect_pass, get_pass_intervals

import csv
from pathlib import Path

#constants/parameters
from configs.config import load_configs
cfg = load_configs()
# unpack config vals
launch_date = cfg.launch_date
launch_site = cfg.launch_site
doppler_data_dir = cfg.doppler_data_dir
orekit_data_path = cfg.orekit_data_path
space_weather_file = cfg.space_weather_file
epoch_utc = cfg.epoch_utc
ecef_frame = cfg.ecef_frame
inertial_frame = cfg.inertial_frame
position_m = cfg.position_m
velocity_mps = cfg.velocity_mps
area_m2 = cfg.area_m2
cd = cfg.cd
mass_kg = cfg.mass_kg
stations = cfg.stations

# init orekit
from src.setup import setup_orekit
setup_orekit()

#import orekit libraries
import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.frames import FramesFactory
from org.orekit.utils import PVCoordinates, Constants, IERSConventions
from org.orekit.orbits import CartesianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState, BoundedPropagator, EphemerisGenerator
from org.orekit.propagation.numerical import NumericalPropagator
from org.orekit.bodies import GeodeticPoint
from org.orekit.propagation.events import ElevationDetector, EventsLogger
from org.orekit.propagation.analytical.tle import TLE
from org.orekit.propagation.analytical.tle.generation import FixedPointTleGenerationAlgorithm
from org.orekit.propagation.events import ExtremumApproachDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent

#import perturbation functions
from .j2_model import build_j2_perturbation_model as j2
from .drag_model import build_drag_force_model as drag
from .satellite_passes import detect_pass, get_pass_intervals, get_max_elevations

#return state from initial rv that we can use for propagation 
def initial_state_ECEF(Rx, Ry, Rz, Vx, Vy, Vz, epoch, frame, inertial_frame,muE,mass):
    #state vector given in ECEF (an earth fixed frame), we need to transform to 
    # ECI (intertial/non-rotating) frame for propagation
    rv_ecef = PVCoordinates(Vector3D(Rx, Ry, Rz),
                            Vector3D(Vx, Vy, Vz))
    rv_eci= frame.getTransformTo(inertial_frame, epoch).transformPVCoordinates(rv_ecef)
    orbit = CartesianOrbit(rv_eci,inertial_frame,epoch,muE)
    initial_state = SpacecraftState(orbit,mass)
    return initial_state


def get_state(ephemeris, start_date, end_date, fixed_frame, state_csv_path, step_size_sec):
    """
    Write propagated state to CSV at each step. step_size_sec (seconds) should match
    the propagator integrator step so the CSV has one row per propagated value.
    """
    state_csv = Path(state_csv_path)

    with state_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Date (UTC)", "Rx (m)", "Ry (m)", "Rz (m)", "Vx (m/s)", "Vy (m/s)", "Vz (m/s)" ])
        t = start_date

        while t.compareTo(end_date) <= 0:
            state = ephemeris.propagate(t)
            pos = state.getPVCoordinates(fixed_frame).getPosition()
            vel = state.getPVCoordinates(fixed_frame).getVelocity()
            writer.writerow([
                t.toString(TimeScalesFactory.getUTC())[:23],  # keep only 0.000 seconds
                pos.getX(), pos.getY(), pos.getZ(),
                vel.getX(), vel.getY(), vel.getZ()])
            t = t.shiftedBy(step_size_sec)

    return state_csv



#propagate and get updated TLEs before each pass
#log predicted time of each pass
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
        csv_path, 
        tle_path,
        state_path):
    
    """
    Retrurns:
    - TLE file
    - csv file of pass indexes, AOS time, LOS time, TLE epoch time, max elevation for each pass
    """
    utc = TimeScalesFactory.getUTC()

    rx,ry,rz,vx,vy,vz = position[0], position[1], position[2], velocity[0], velocity[1], velocity[2]

    #define orbit and initial state
    state0=initial_state_ECEF(rx,ry,rz,vx,vy,vz,epoch,fixed_frame,inertial_frame,muE,mass)

    #create propegator and add perturbations
    step_size = 5.0 #smaller for LEO orbits
    integrator = ClassicalRungeKuttaIntegrator(step_size)
    prop = NumericalPropagator(integrator)
    prop.setOrbitType(OrbitType.CARTESIAN)
    prop.setInitialState(state0)
    prop.addForceModel(j2(fixed_frame))
    prop.addForceModel(drag(fixed_frame, area, cd))

    #detect and collect pass intervals over the week
    passes,topo = detect_pass(gs_name, gs_lat, gs_long, gs_alt, gs_min_elev, fixed_frame)
    pass_logger = EventsLogger()
    prop.addEventDetector(pass_logger.monitorDetector(passes))

    #detect and collect max elevation for each pass
    max_det = ExtremumApproachDetector(topo).withHandler(ContinueOnEvent())
    max_el_logger = EventsLogger()
    prop.addEventDetector(max_el_logger.monitorDetector(max_det))

    #propagate over window, use ephemeris to pull states at each pass
    ephGen = prop.getEphemerisGenerator()
    end = epoch.shiftedBy(days*86400.0)
    prop.propagate(epoch,end)

    ephem = ephGen.getGeneratedEphemeris();
    
    #store passes and max elevation after propagation
    intervals = get_pass_intervals(pass_logger)
    max_el_list = get_max_elevations(max_el_logger, intervals, topo, fixed_frame)
    

    # template TLE placeholders, 69 characters perline 
    template_line1 = "1 99999U 26001A   26054.50000000  .00000000  00000-0  00000-0 0  9991"
    template_line2 = "2 99999  97.5000  0.0000 0001000   0.0000   0.0000 15.00000000    01"
    template_TLE = TLE(template_line1, template_line2)

    generator = FixedPointTleGenerationAlgorithm()

    #store tles 
    pass_rows = []
    for idx, (aos, los) in enumerate(intervals, start=1):
        tle_epoch = aos.shiftedBy(-600.0) #tle epoch is 10 mins before aos
        state_at_epoch = ephem.propagate(tle_epoch)  #get state at each epoch from ephemeris
        tle = generator.generate(state_at_epoch, template_TLE)

        pass_rows.append({
            "index": idx,
            "aos": aos,
            "los": los,
            "max_elevation": max_el_list[idx - 1]["max_el_deg"],
            "az_at_max_elev": max_el_list[idx - 1]["az_at_max_el"],
            "tle_epoch": tle_epoch,
            "line1": tle.getLine1(),
            "line2": tle.getLine2(),
        })

    #write csv file
    csv_path = Path(csv_path)
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Pass #", "AOS (UTC)", "LOS (UTC)", "TLE Epoch (UTC)","Max Elevation(deg)", "Azimuth at Max Elevation(deg)"])
        for r in pass_rows:
            writer.writerow([
                r["index"],
                r["aos"].toString(utc)[:23], #keep only 0.000 seconds
                r["los"].toString(utc)[:23],
                r["tle_epoch"].toString(utc)[:23],
                f"{r['max_elevation']:.2f}",
                f"{r['az_at_max_elev']:.2f}"
            ])

    #write tle file        
    tle_path = Path(tle_path)
    with tle_path.open("w", newline="\n") as fh:
        for r in pass_rows:
            fh.write(r["line1"].rstrip() + "\n")
            fh.write(r["line2"].rstrip() + "\n\n")

    #write state csv file (one row per integrator step)
    states_csv = get_state(ephem, epoch, end, fixed_frame, state_path, step_size)

    return csv_path, tle_path, states_csv


