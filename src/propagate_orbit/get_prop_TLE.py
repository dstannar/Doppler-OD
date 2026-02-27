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

ROOT = Path(__file__).resolve().parents[2]  # .../Doppler-OD
sys.path.insert(0, str(ROOT))

#initialize
import os, sys, string, math
import numpy as np
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
frame = cfg.frame
position_m = cfg.position_m
velocity_mps = cfg.velocity_mps
area_m2 = cfg.area_m2
cd = cfg.cd
mass_kg = cfg.mass_kg
stations = cfg.stations

# init orekit
from setup import setup_orekit
setup_orekit(orekit_data_path)

#import orekit libraries
import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.frames import FramesFactory, ITRFVersion, IERSConventions
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.frames import FramesFactory
from org.orekit.utils import PVCoordinates, Constants
from org.orekit.orbits import CartesianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.numerical import NumericalPropagator
from org.orekit.bodies import GeodeticPoint
from org.orekit.propagation.events import ElevationDetector, EventsLogger
from org.orekit.propagation.analytical.tle import TLE


#import perturbation functions
#from j2_model import build_j2_perturbation_model as j2
#from drag_model import build_drag_force_model as drag
from satellite_passes import detect_pass, get_pass_intervals





def initial_state_ECEF(Rx, Ry, Rz, Vx, Vy, Vz, epoch, frame, inertial_frame,muE,mass):
    #state vector given in ECEF (an earth fixed frame), we need to transform to 
    # ECI (intertial/non-rotating) frame for propagation
    rv_ecef = PVCoordinates(Vector3D(Rx, Ry, Rz),
                            Vector3D(Vx, Vy, Vz))
    rv_eci= frame.getTransformTo(inertial_frame, epoch).transformPVCoordinates(rv_ecef)
    orbit = CartesianOrbit(rv_eci,inertial_frame,epoch,muE)
    initial_state = SpacecraftState(orbit,mass)
    return initial_state


def get_TLEs(
        position,velocity,epoch,inertial_frame, fixed_frame,muE,
        gs_name, gs_lat, gs_long, gs_alt, gs_min_elev,
        days,mass,
        csv_path, tle_path):
    
    # mass, area, cd, rho0, h0, H
    """
    Retrurns:
    - TLE file
    - passes, TLEs
    """

    utc = TimeScalesFactory.getUTC()

    rx,ry,rz,vx,vy,vz = position[0], position[1], position[2], velocity[0], velocity[1], velocity[2]

    #define orbit and initial state
    state0=initial_state_ECEF(rx,ry,rz,vx,vy,vz,epoch,fixed_frame,inertial_frame,muE,mass)

    #create propegator and add perturbations
    step_size = 30.0 #smaller for LEO orbits
    integrator = ClassicalRungeKuttaIntegrator(step_size)
    prop = NumericalPropagator(integrator)
    prop.setOrbitType(OrbitType.CARTESIAN)
    prop.setInitialState(state0)
    #prop.addForceModel(j2)
    #prop.addForceModel(drag)

    #detect and collect pass intervals over the week
    passes = detect_pass(gs_name, gs_lat, gs_long, gs_alt, gs_min_elev, fixed_frame)
    logger = EventsLogger()
    prop.addEventDetector(logger.monitorDetector(passes))

    #propagate over window
    end = epoch.shiftedBy(days*86400.0)
    prop.propagate(epoch,end)
    
    intervals = get_pass_intervals(logger)

    #make TLE template for statetoTLE conversion
    template_line1 = "1 99999U 26001A   26054.50000000  .00000000  00000-0  00000-0 0  9991"
    template_line2 = "2 99999  97.5000  0.0000 0001000   0.0000   0.0000 15.00000000    01"
    template_TLE = TLE(template_line1, template_line2)

    #convert state to TLEs, append tles for aos/los inside intervals
    pass_rows = []
    for idx, (aos,los) in enumerate(intervals, start=1):
        tle_epoch = aos.shiftedBy(-10*60) #get TLE 10 mins before AOS
        state_at_epoch = prop.prpagate(tle_epoch)
        tle = TLE.stateToTLE(state_at_epoch, template_TLE)

        pass_rows.append({
            "index": idx,
            "aos": aos,
            "los": los,
            "epoch": tle_epoch,
            "Line1": tle.getLine1(),
            "Line2": tle.getLine2()
        })

    #write csv for passes
    csv_path = Path(csv_path)
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pass_index", "aos_utc", "los_utc", "tle_epoch_utc"])
        for r in pass_rows:
            writer.writerow([
                r["index"],
                r["aos"].toString(utc),
                r["los"].toString(utc),
                r["tle_epoch"].toString(utc),
            ])

    #write tle file        
    tle_path = Path(tle_path)
    with tle_path.open("w", newline="\n") as fh:
        for r in pass_rows:
            fh.write(r["line1"].rstrip() + "\n")
            fh.write(r["line2"].rstrip() + "\n\n")

    return pass_rows, csv_path, tle_path








