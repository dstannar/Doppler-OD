"""
This script will build define our ground station as a topocentric frame, use an event detector
for the ground station when the satellite will be within line of sight of the antennas. Orekit
has a practical class that can extract event of a pass of a satellite based on ground station
location and pointing elevation. Then, using this event detector, we will use event logger to
give us time intervals from AOS (aquisition of signal) to LOS (loss of signal). This interval
signifies a "pass". We will calculate the first aos/los epochs after launch and propagate the
state vector to those epochs. Note one single propagated TLE could be used to feed into Satnet,
but repeatability of new TLE every pass allows for more accurate estimations over the first week
of passes (accounting for how perturbations are changing over time).

Inputs:
-

Outputs:
-

"""

#initialize
import math

#import orekit libraries
import orekit
from orekit.pyhelpers import setup_orekit_curdir

from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint
from org.orekit.utils import IERSConventions, Constants
from org.orekit.propagation.events import ElevationDetector, EventsLogger


#build ground station and event detector for satellite passes
def detect_pass(name, latitude, longtiude, altitude, marconi_min_elevation):
    """
    Builds the ground station TopocentricFrame and an ElevationDetector configured to trigger
    when satellite elevation crosses a minimum elevation mask.

    Args:
        name (str): Station name
        latitude (float): degrees
        longtiude (float): degrees  (keeping your spelling)
        altitude (float): meters
        marconi_min_elevation (float): degrees (minimum elevation mask)

    Returns:
        tuple: (earth, station_frame, elevation_detector)
    """

    #see GeodeticPoint to define ground station location point
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longtiude)
    gp = GeodeticPoint(lat_rad, lon_rad, altitude)

    #use orekit TopocentricFrame to define ground station frame
    itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
    earth = OneAxisEllipsoid(
        Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
        Constants.WGS84_EARTH_FLATTENING,
        itrf
    )
    station_frame = TopocentricFrame(earth, gp, name)

    #use orekit ElevationDetector.withConstantElevation to set up minimum elevation for detection
    elev_mask_rad = math.radians(marconi_min_elevation)
    detector = ElevationDetector(station_frame).withConstantElevation(elev_mask_rad)

    return earth, station_frame, detector  #detected event/pass



#extract interval for aos/los from event detector
def get_pass_intervals(event_logger):
    """
    Convert EventsLogger logged events (from an ElevationDetector) into AOS/LOS intervals.

    Convention (typical for ElevationDetector with constant elevation mask):
        - isIncreasing() == True  -> AOS (rising through mask)
        - isIncreasing() == False -> LOS (falling through mask)

    Args:
        event_logger (EventsLogger): Orekit EventsLogger after propagation

    Returns:
        list: list of (aos_date, los_date) AbsoluteDate pairs
    """

    #use EventLogger to extraxt time intervals for aos/los
    logged = event_logger.getLoggedEvents()

    intervals = []
    current_aos = None

    for i in range(logged.size()):
        ev = logged.get(i)
        date = ev.getState().getDate()
        increasing = ev.isIncreasing()

        if increasing:
            # AOS
            current_aos = date
        else:
            # LOS
            if current_aos is not None:
                intervals.append((current_aos, date))
                current_aos = None

    return intervals  #intervals