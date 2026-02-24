"""
Convert doppler observations into Orekit measurements for BatchLSEstimator.

- Take the loaded doppler data (time_utc, station_id, doppler_hz and ground-station definitions from config.
- Build Orekit ObservedMeasurement instances for range-rate Convert doppler Hz to range rate; 
- Register each measurement with its time and station so Orekit's
  BatchLSEstimator can compute predicted values and partials internally (STM
  and measurement sensitivity are handled by Orekit).
"""

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