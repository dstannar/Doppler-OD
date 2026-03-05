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
epoch_utc = cfg.epoch_utc # ISO-8601 string
epoch = cfg.epoch # Absolute Date
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



from src.propagate_orbit.get_prop_TLE import get_TLEs

# ECEF/inertial/epoch in SALE.yaml are Python expressions; evaluate after Orekit is ready.
utc = TimeScalesFactory.getUTC()
_orekit_globals = {
    "FramesFactory": FramesFactory,
    "ITRFVersion": ITRFVersion,
    "IERSConventions": IERSConventions,
    "AbsoluteDate": AbsoluteDate,
    "utc": utc,
}
def _eval_orekit(s):
    return s if not isinstance(s, str) else eval(s, _orekit_globals)

ecef = _eval_orekit(cfg.ecef_frame)
inertial = _eval_orekit(cfg.inertial_frame)
epoch = _eval_orekit(cfg.epoch)
# orekit uses ITRF, a type of ECEF frame
muE = Constants.WGS84_EARTH_MU  # m^3/s^2


#define Marconi station params
Marconi = stations["Marconi"]
Marconi_lat = Marconi.lat_deg
Marconi_lon = Marconi.lon_deg
Marconi_alt = Marconi.alt_m
marconi_min_elevation = Marconi.min_elevation_deg


passes_csv, tle_path_out, states_csv = get_TLEs(
    position=position_m,
    velocity =velocity_mps,
    epoch=epoch,
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
    tle_path = "passes.tle",
    state_path = "states.csv"
    
             )















