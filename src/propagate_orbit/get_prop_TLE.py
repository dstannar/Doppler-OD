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

#initialize
import os, sys, string, math
import numpy as np
# init orekit
from setup import setup_orekit
setup_orekit()

#import orekit libraries
import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator

from org.orekit.frames import FramesFactory, ITRFVersion, IERSConventions
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.utils import PVCoordinates, Constants
from org.orekit.orbits import CartesianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.numerical import NumericalPropagator


#import perturbation functions
from j2_model import build_j2_perturbation_model as j2
from drag_model import build_drag_force_model as drag
from satellite_passes import detect_pass, get_pass_intervals

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


def initial_state_ITRF(Rx, Ry, Rz, Vx, Vy, Vz, epoch, frame, inertial_frame,muE):
    #state vector given in ECEF (an earth fixed frame), transform to ECI (intertial) frame for propagation
    rv_ecef = PVCoordinates(Vector3D(Rx, Ry, Rz),
                            Vector3D(Vx, Vy, Vz))
    rv_eci= frame.getTransformTo(inertial_frame, epoch).transformPVCoordinates(rv_ecef)
    orbit = CartesianOrbit(rv_eci,inertial_frame,epoch,muE)
    initial_state = SpacecraftState(orbit,mass_kg)
    return initial_state

def get_TLEs(prelaunch_position,prelaunch_velocity,epoch,frame,mass):

    #define given
    #state vector from SpaceX prelaunch ODM
    pre_pos = [5005113.445, 4606039.088, -1129194.884] #m, ECEF
    pre_vel = [1914.034, -268.470, 7437.840] #m/s, ECEF
    rx,ry,rz,vx,vy,vz = pre_pos[0], pre_pos[1], pre_pos[2], pre_vel[0], pre_vel[1], pre_vel[2]
    pre_epoch=

    #define constants and parameters
    ecef = FramesFactory.getITRF(ITRFVersion.ITRF_2020,IERSConventions.IERS_2010, True)
    inertial = inertial = FramesFactory.getEME2000()
    muE=Constants.IERS2010_EARTH_MU
    step_size=30.0 #smaller for LEO orbits

    #define orbit and initial state
    state0=initial_state_ITRF(rx,ry,rz,vx,vy,vz,epoch,ecef,inertial,muE)

    #create propegator and add perturbations
    integrator = ClassicalRungeKuttaIntegrator(step_size)
    prop = NumericalPropagator(integrator)
    prop.setOrbitType(OrbitType.CARTESIAN)
    prop.setInitialState(state0)
    prop.addForceModel(j2)
    prop.addForceModel(drag)

    #detect and collect pass intervals over the week
    passes = detect_pass()
    log_passes = EventsLogger()
    prop.addEventDetector(log_passes.monitorDetector(passes))
    intervals = get_pass_intervals(log_passes)

    #propagate 
    pass_date

    #make TLE templerate

    #convert state to TLEs, append tles for aos/los inside intervals


    return #TLEs and time of each pass after launch





