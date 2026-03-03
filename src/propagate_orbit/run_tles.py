#unit test

from pathlib import Path
import sys


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
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.numerical import NumericalPropagator
from org.orekit.bodies import GeodeticPoint
from org.orekit.propagation.events import ElevationDetector, EventsLogger
from org.orekit.propagation.analytical.tle import TLE



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

from src.propagate_orbit.get_prop_TLE import get_TLEs

#define constants and parameters
ecef = FramesFactory.getITRF(ITRFVersion.ITRF_2020,IERSConventions.IERS_2010, True)
    #orekit uses itrf, which is a type of ecef frame, but for simplicity we wil call it ecef
inertial = FramesFactory.getEME2000()
utc = TimeScalesFactory.getUTC()
muE=Constants.WGS84_EARTH_MU #m^3/s^2

#from SpaceX prelaunch ODM
pre_pos = [5005113.445, 4606039.088, -1129194.884] #m, ECEF
pre_vel = [1914.034, -268.470, 7437.840] #m/s, ECEF
pre_epoch=AbsoluteDate(2026, 3, 29, 11, 17, 1.208,utc)

#define Marconi station params
Marconi = stations["Marconi"]
Marconi_lat = Marconi.lat_deg
Marconi_lon = Marconi.lon_deg
Marconi_alt = Marconi.alt_m
marconi_min_elevation = Marconi.min_elevation_deg


passes, tles = get_TLEs(
    position=pre_pos,
    velocity =pre_vel,
    epoch=pre_epoch,
    inertial_frame=inertial, 
    fixed_frame=ecef,
    muE=muE,
    gs_name="Marconi",
    gs_lat=Marconi_lat,
    gs_long=Marconi_lon,
    gs_alt=Marconi_alt,
    gs_min_elev=marconi_min_elevation,
    days=10,
    mass = mass_kg,
    area=area_m2, 
    cd=cd,
    csv_path = "passes.csv",
    tle_path = "passes.tle"
    
             )















