"""
Convert doppler observations into Orekit measurements for BatchLSEstimator.

- Take the loaded doppler data (time_utc, station_id, doppler_hz) and
  ground-station definitions from config.
- Build Orekit ObservedMeasurement instances for range-rate; convert Doppler
  Hz to range rate (m/s).
- Each measurement has time and station so BatchLSEstimator can compute
  predicted values and partials internally (STM and measurement sensitivity
  are handled by Orekit).
"""


def build_ground_stations(stations_config, frame):
    """
    Build Orekit GroundStation objects from config for use in RangeRate measurements.

    Parameters
    ----------
    stations_config : dict
        Station name -> {lat_deg, lon_deg, alt_m, ...}; from config.stations.
    frame : Orekit Frame
        Reference frame for topocentric frames

    Returns
    -------
    dict[str, GroundStation]
        station_id -> Orekit GroundStation
    """


def doppler_hz_to_range_rate(doppler_hz, freq_tx_hz):
    """
    Convert one-way Doppler shift (Hz) to range rate (m/s).

    range_rate = -(doppler_hz / freq_tx_hz) * c  (approaching -> positive range rate
    if that matches Orekit RangeRate convention).

    Parameters
    ----------
    doppler_hz : float
        Observed Doppler shift in Hz (sign: positive = approaching).
    freq_tx_hz : float
        Nominal transmitter frequency in Hz.

    Returns
    -------
    float
        Range rate in m/s.
    """


def build_range_rate_measurements(doppler_records, ground_stations_map, freq_tx_hz, sigma_range_rate_mps):
    """
    Build list of Orekit RangeRate (ObservedMeasurement) from Doppler records.

    Parameters
    ----------
    doppler_records : list of dict or structured array
        Each item: time_utc, station_id, doppler_hz (optional: sigma_hz).
    ground_stations_map : dict[str, GroundStation]
        From build_ground_stations.
    freq_tx_hz : float
        Nominal transmitter frequency for Hz -> m/s conversion.
    sigma_range_rate_mps : float or list
        Single sigma (m/s) for all obs, or per-observation sigmas.

    Returns
    -------
    list of Orekit ObservedMeasurement (RangeRate)
        One per record; ready for BatchLSEstimator.addMeasurement().
    """


def get_measurements(doppler_data_dir, stations_config, frame, freq_tx_hz, sigma_range_rate_mps):
    """
    High-level: load Doppler data, build ground stations, build RangeRate measurements.

    Parameters
    ----------
    doppler_data_dir : str
        Path to Doppler CSV root (e.g. SALE-Doppler); subdirs per station.
    stations_config : dict
        Station name -> {lat_deg, lon_deg, alt_m, ...}.
    frame : Orekit Frame
        Reference frame for ground stations.
    freq_tx_hz : float
        Transmitter frequency for Doppler -> range rate.
    sigma_range_rate_mps : float
        Measurement noise sigma in m/s (or per-obs if supported).

    Returns
    -------
    ground_stations : dict[str, GroundStation]
        station_id -> GroundStation.
    measurements : list of ObservedMeasurement
        RangeRate list for batch_ls_OD.run_batch_ls.
    """