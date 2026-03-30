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

#initialize
# init orekit
from src.setup import setup_orekit
setup_orekit()


from configs.config import load_configs
cfg = load_configs()
# unpack config vals
launch_date = cfg.launch_date
launch_site = cfg.launch_site
doppler_data_dir = cfg.doppler_data_dir
orekit_data_path = cfg.orekit_data_path
space_weather_file = cfg.space_weather_file
epoch_utc = cfg.epoch_utc
ecef_frame = cfg.ecef_frame
inertial_frame = cfg.inertial_frame
position_m = cfg.position_m
velocity_mps = cfg.velocity_mps
area_m2 = cfg.area_m2
cd = cfg.cd
mass_kg = cfg.mass_kg
stations = cfg.stations

#Necessary Imports
import math
import csv
from pathlib import Path
from org.orekit.estimation.measurements import GroundStation, RangeRate, ObservableSatellite
from org.orekit.bodies import CelestialBodyFactory
from org.orekit.utils import Constants
from org.orekit.bodies import GeodeticPoint, OneAxisEllipsoid
from org.orekit.time import AbsoluteDate,TimeScalesFactory
from org.orekit.frames import TopocentricFrame




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
    earth = OneAxisEllipsoid(
    Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    Constants.WGS84_EARTH_FLATTENING,
    frame
)
    ground_stations = {}
    for station_id, s in stations_config.items():
        lat_rad = math.radians(float(s.lat_deg))
        lon_rad = math.radians(float(s.lon_deg))
        alt_m = float(s.alt_m)

        point = GeodeticPoint(lat_rad, lon_rad, alt_m)
        topo = TopocentricFrame(earth, point, station_id)
        ground_stations[station_id] = GroundStation(topo)
    return ground_stations


    



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
    Range_rate = -(float(doppler_hz) / float(freq_tx_hz)) * Constants.SPEED_OF_LIGHT

    return Range_rate


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
    utc = TimeScalesFactory.getUTC()
    satellite = ObservableSatellite(0)
    measurements = []

    for rec in doppler_records:
        station = ground_stations_map[rec["station_id"]]
        date = AbsoluteDate(rec["time_utc"].replace("Z",""), utc)
        
        range_rate = doppler_hz_to_range_rate(
            rec["doppler_hz"],
            freq_tx_hz
        )
        meas = RangeRate(
            station,
            date,
            range_rate,
            sigma_range_rate_mps,
            1.0,
            False,
            satellite
        )

        measurements.append(meas)
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
    ground_stations = build_ground_stations(stations_config,frame)
    doppler_records = []

    for csv_file in Path(doppler_data_dir).rglob("*.csv"):

        station_id = csv_file.parent.name

        with open(csv_file, "r", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                doppler_records.append({
                    "time_utc": row["time_utc"],
                    "station_id": station_id,
                    "doppler_hz": float(row["doppler_hz"]),
                })

    measurements = build_range_rate_measurements(
        doppler_records,
        ground_stations,
        freq_tx_hz,
        sigma_range_rate_mps
    )

    return ground_stations, measurements