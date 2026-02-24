"""
doppler_from_TLE.py
Compute predicted doppler from a TLE at ground stations

- Given a TLE and a list of ground stations (from config), propagate the TLE
  with Orekit over the observation times from the recorded doppler profile.
- Compute the line-of-sight range rate at each time and station and convert to
  doppler shift in Hz (same sign convention as the observed profile: positive =
  approaching).
- Return predicted doppler time series per station so compute_LS_cost.py can form
  observed-minus-predicted residuals.
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
