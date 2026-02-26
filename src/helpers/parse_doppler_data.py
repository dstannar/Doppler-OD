"""
parse_doppler_data.py
Load and validate doppler profile CSV data.

- Load doppler CSV(s) from the doppler_data_dir and station subdirs
  (SALE-Doppler/Marconi/, SALE-Doppler/EEDepartment/).
- Parse into a flat list of records (time_utc, station_id, doppler_hz) for
  use by which_TLE and doppler_OD.
- Validate station names against config (stations.yaml). Support one file per
  pass per station.
- Document and enforce the CSV format (columns, units, sign convention:
  positive doppler = satellite approaching the station).
"""


def load_doppler_records(doppler_data_dir, stations_config):
    """
    Load Doppler CSV(s) from directory and station subdirs; return flat records.

    Scan doppler_data_dir and station subdirs; parse CSVs into a common
    structure. Validate station names against stations_config. One file per
    pass per station. Output aligns with doppler_OD doppler_records format.

    Parameters
    ----------
    doppler_data_dir : path-like
        Root path (e.g. SALE-Doppler); subdirs per station.
    stations_config : dict
        Station name -> {lat_deg, lon_deg, alt_m, ...}; used to validate
        station names.

    Returns
    -------
    list of dict or structured array
        Flat list of records, each with time_utc, station_id, doppler_hz
        (optional: sigma_hz). Same format as measurement_model doppler_records.
    """
    ...
