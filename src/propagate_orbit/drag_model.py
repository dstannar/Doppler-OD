"""
    LEO Drag Force Model
 
    Returns a drag force using [any atmospheric model] that accounts for the atmospheric LEO drag that
    SAL-E will experience after being deployed at 510km altitude.
 
    *note: orekit has existing drag force models and LEO atmospheric density models that can be used
    within the script.
 
 
    Inputs:
        - reference frame (should be in ECEF)
        - atmospheric model
        - area
        -drag_coef
        -mass
 
    Outputs:
        - drag_force_model
"""
 
#initialize
# init orekit
from src.setup import setup_orekit
setup_orekit()

#import libraries
from org.orekit.forces.drag import DragForce, IsotropicDrag
from org.orekit.utils import Constants
from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory
from org.orekit.models.earth.atmosphere import NRLMSISE00
from org.orekit.models.earth.atmosphere.data import CssiSpaceWeatherData
from org.orekit.data import DataSource
from org.orekit.time import TimeScalesFactory
 
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
stations = cfg.stations # namespace dict
 
#drag force function
def build_drag_force_model(frame,area, drag_coef,atmosphere=None):
     #If atmosphere is None:
     #builds Earth ellipsoid (WGS84) in the provided Earth-fixed frame
     #inputs CSSI space weather data
     #builds NRLMISE-00 atmosphere model
    if atmosphere is None:
        earth = OneAxisEllipsoid(
            Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
            Constants.WGS84_EARTH_FLATTENING,
            frame
        )
        
        utc = TimeScalesFactory.getUTC()

        ds = DataSource(space_weather_file)
        sw = CssiSpaceWeatherData(ds, utc)  
        sun = CelestialBodyFactory.getSun()
        atmosphere = NRLMSISE00(sw,sun,earth,utc)
       
        #drag perturbation force model
        return DragForce(atmosphere, IsotropicDrag(area, drag_coef))
 
   
 