"""
    LEO Drag Force Model

    Returns a drag force using [any atmospheric model] that accounts for the atmospheric LEO drag that 
    SAL-E will experience after being deployed at 510km altitude.

    *note: orekit has existing drag force models and LEO atmospheric density models that can be used
    within the script. 


    Inputs:
        - reference frame (should be in ECEF)
        - atmospheric model

    Outputs:
        - 
"""

#initialize
# init orekit
from setup import setup_orekit
setup_orekit()

#import libraries


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
def build_drag_force_model(frame, atmosphere, area, drag_coef,mass):



    return #drag force 
    