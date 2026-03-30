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

from __future__ import annotations

from math import radians
from typing import Sequence, Union

import numpy as np
from org.orekit.bodies import GeodeticPoint, OneAxisEllipsoid
from org.orekit.estimation.measurements import GroundStation, ObservableSatellite, RangeRate
from org.orekit.frames import TopocentricFrame
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import Constants

from src.helpers.parse_doppler_data import load_doppler_records

C_LIGHT = 299792458.0


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
    r_earth = Constants.WGS84_EARTH_EQUATORIAL_RADIUS
    flat = Constants.WGS84_EARTH_FLATTENING
    earth = OneAxisEllipsoid(r_earth, flat, frame)
    out = {}
    for name, s in stations_config.items():
        gp = GeodeticPoint(radians(float(s.lat_deg)), radians(float(s.lon_deg)), float(s.alt_m))
        topo = TopocentricFrame(earth, gp, str(name))
        out[str(name)] = GroundStation(topo)
    return out


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
    return -(float(doppler_hz) / float(freq_tx_hz)) * C_LIGHT


def _np_datetime64_to_absolutedate(dt) -> AbsoluteDate:
    utc = TimeScalesFactory.getUTC()
    d = np.datetime64(dt)
    s = str(d)
    if "T" not in s and " " in s:
        s = s.replace(" ", "T", 1)
    return AbsoluteDate(s, utc)


def _sort_records_by_time(records: np.ndarray) -> np.ndarray:
    arr = np.asarray(records, dtype=object)
    n = len(arr)
    if n == 0:
        return arr
    keys = np.array([np.datetime64(arr[i][1]) for i in range(n)])
    return arr[np.argsort(keys)]


def build_range_rate_measurements(
    doppler_records,
    ground_stations_map,
    freq_tx_hz,
    sigma_range_rate_mps: Union[float, Sequence[float]],
):
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
    sat = ObservableSatellite(0)
    arr = np.asarray(doppler_records, dtype=object)
    n = len(arr)
    if isinstance(sigma_range_rate_mps, (int, float)):
        sigmas = [float(sigma_range_rate_mps)] * n
    else:
        sigmas = [float(x) for x in sigma_range_rate_mps]
        if len(sigmas) != n:
            raise ValueError(
                f"sigma_range_rate_mps length {len(sigmas)} does not match number of observations {n}"
            )

    measurements = []
    weight = 1.0
    for i in range(n):
        row = arr[i]
        station_id = str(row[0])
        time_utc = row[1]
        doppler_hz = float(row[2])
        if station_id not in ground_stations_map:
            raise KeyError(f"No GroundStation for station_id={station_id!r}")
        gs = ground_stations_map[station_id]
        rr = doppler_hz_to_range_rate(doppler_hz, freq_tx_hz)
        date = _np_datetime64_to_absolutedate(time_utc)
        measurements.append(
            RangeRate(gs, False, date, rr, sigmas[i], weight, sat)
        )
    return measurements


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
    records = load_doppler_records(doppler_data_dir, stations_config)
    records = _sort_records_by_time(records)
    ground_stations = build_ground_stations(stations_config, frame)
    measurements = build_range_rate_measurements(
        records, ground_stations, freq_tx_hz, sigma_range_rate_mps
    )
    return ground_stations, measurements
