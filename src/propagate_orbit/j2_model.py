"""
J2 Perturbation Model

Returns a gravity force model that accounts for J2 perturbations (Earth's equatorial bulge).
All 

Inputs:
- Reference frame (should be ECEF)

Outputs:
- 

"""
#initialize
# init orekit
from setup import setup_orekit
setup_orekit()

#import libraries


#define constants
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

#J2 pertubation function
def build_j2_perturbation_model(frame, altitude):



    return #J2 perturbation model