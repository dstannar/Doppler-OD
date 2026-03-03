"""
doppler_from_TLE.py
Compute predicted doppler from a TLE at ground stations.

- Given a TLE and a list of ground stations (from config), propagate the TLE
  with Orekit over the observation times from the recorded doppler profile.
- Compute the line-of-sight range rate at each time and station and convert to
  doppler shift in Hz (same sign convention as the observed profile: positive =
  approaching).
- Return predicted doppler aligned 1:1 with input records for residual computation.
"""

from configs.config import load_configs

cfg = load_configs()
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


def predict_doppler(tle, doppler_records, stations_config, frame, freq_tx_hz):
    """
    Predict Doppler (Hz) from a TLE at each observation time and station.

    Propagate TLE to each time_utc, compute line-of-sight range rate at that
    station, convert to Doppler Hz (positive = approaching). Reuse Orekit for
    propagation and range-rate; use inverse of doppler_hz_to_range_rate for
    consistency with measurement_model.

    Parameters
    ----------
    tle : Orekit TLE
        TLE to propagate.
    doppler_records : list of dict or structured array
        Each item: time_utc, station_id, doppler_hz (same order as output).
    stations_config : dict
        Station name -> {lat_deg, lon_deg, alt_m, ...}; from config.stations.
    frame : Orekit Frame
        Reference frame for propagation and station positions.
    freq_tx_hz : float
        Transmitter frequency in Hz (e.g. from config.frequency_hz).

    Returns
    -------
    array or list
        Predicted Doppler in Hz, same length and order as doppler_records.
    """
    ...
