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

import math

import numpy as np

# orekit imports
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint
from org.orekit.utils import Constants
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.propagation.analytical.tle import TLEPropagator


def _build_station_positions(stations_config, frame):
    """Build dict of station_id -> position Vector3D in the given frame (e.g. ECEF)."""

    rE = Constants.WGS84_EARTH_EQUATORIAL_RADIUS
    flatE = Constants.WGS84_EARTH_FLATTENING
    earth = OneAxisEllipsoid(rE, flatE, frame)
    out = {}
    for name, st in stations_config.items():
        lat_rad = math.radians(st.lat_deg)
        lon_rad = math.radians(st.lon_deg)
        alt_m = st.alt_m
        gp = GeodeticPoint(lat_rad, lon_rad, alt_m)
        out[name] = earth.transform(gp)
    return out



def range_rate_to_doppler_hz(range_rate_mps, freq_tx_hz):
    """
    Convert line-of-sight range rate (m/s) to Doppler shift (Hz).
    Parameters
    ----------
    range_rate_mps : float
        Line-of-sight range rate in m/s
    freq_tx_hz : float
        Transmitter frequency in Hz.

    Returns
    -------
    float
        Doppler shift in Hz (positive = approaching).
    """
    c = Constants.SPEED_OF_LIGHT
    return -range_rate_mps * freq_tx_hz / c


def predict_doppler(tle, doppler_records, stations_config, frame, freq_tx_hz):
    """
    Predict Doppler (Hz) from a TLE at each observation time and station.

    Propagate TLE to each time_utc, compute line-of-sight range rate at that
    station, convert to Doppler Hz (positive = approaching).

    Parameters
    ----------
    tle : Orekit TLE
        TLE to propagate.
    doppler_records : structured array
        Each item: time_utc, station_id, doppler_hz
    stations_config : dict
        Station name -> {lat_deg, lon_deg, alt_m}; from config.stations.
    frame : Orekit Frame
        Reference frame for propagation and station positions (ECEF).
    freq_tx_hz : float
        Transmitter frequency in Hz (from config.frequency_hz).

    Returns
    -------
    array or list
        Predicted Doppler in Hz, same length and order as doppler_records.
    """

    # Use the given frame for propagation and station positions (ECEF).
    station_positions = _build_station_positions(stations_config, frame)
    propagator = TLEPropagator.selectExtrapolator(tle)

    predicted = []
    for rec in doppler_records:
        time_utc = rec["time_utc"]
        station_id = rec["station_id"]

        if isinstance(time_utc, np.datetime64):
            time_utc = str(time_utc)
        elif hasattr(time_utc, "isoformat"):
            time_utc = time_utc.isoformat()
        target_date = AbsoluteDate(time_utc, TimeScalesFactory.getUTC())
        pv = propagator.getPVCoordinates(target_date, frame)
        sat_pos = pv.getPosition()
        sat_vel = pv.getVelocity()

        station_pos = station_positions[station_id]
        delta = sat_pos.subtract(station_pos)
        range_m = delta.getNorm()
        if range_m < 1e-6:
            range_rate_mps = 0.0
        else:
            range_rate_mps = delta.normalize().dot(sat_vel)

        doppler_hz = range_rate_to_doppler_hz(float(range_rate_mps), freq_tx_hz)
        predicted.append(doppler_hz)

    return np.asarray(predicted)
