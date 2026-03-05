"""
This script will build define our ground station as a topocentric frame, use an event detector
for the ground station when the satellite will be within line of sight of the antennas. Orekit
has a practical class that can extract event of a pass of a satellite based on ground station 
location and pointing elevation. Then, using this event detector, we will use event logger to 
give us time intervals from AOS (aquisition of signal) to LOS (loss of signal). This interval 
signifies a "pass". We will calculate the first aos/los epochs after launch and propagate the 
state vector to those epochs. 

Note: using a single propagated TLE for the entire first week would result in poor prediction 
due to perturbmations and initial orbit uncertainty. Thus, giving Satnet a new TLE through 
ever pass allows for more accurate estimations over the first week of passes

Inputs:
- 

Outputs:
- 

"""

#initialize
# init orekit
from yaml import events

from src.setup import setup_orekit
setup_orekit()
from math import radians
from math import degrees

#import orekit libraries
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint
from org.orekit.propagation.events import ElevationDetector
from org.orekit.frames import TopocentricFrame
from org.orekit.propagation.events.handlers import ContinueOnEvent
from org.orekit.utils import Constants
from org.orekit.time import AbsoluteDate, TimeScalesFactory

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
ecef_frame = cfg.ecef_frame
inertial_frame = cfg.inertial_frame
position_m = cfg.position_m
velocity_mps = cfg.velocity_mps
area_m2 = cfg.area_m2
cd = cfg.cd
mass_kg = cfg.mass_kg
stations = cfg.stations # namespace dict

rE = Constants.WGS84_EARTH_EQUATORIAL_RADIUS #m
muE = Constants.WGS84_EARTH_MU #m^3/s^2
flatE = Constants.WGS84_EARTH_FLATTENING 

#build ground station and event detector for satellite passes 
def detect_pass(name, latitude, longtiude, altitude, marconi_min_elevation,fixed_frame):

    #build earth
    earth = OneAxisEllipsoid(rE,flatE,fixed_frame)

    #see GeodeticPoint to define ground station location point on earth
    gp = GeodeticPoint(radians(latitude),radians(longtiude),altitude)

    #use orekit TopocentricFrame to define ground station frame
    topo = TopocentricFrame(earth, gp, name)

    #use orekit ElevationDetector.withConstantElevation to set up minimum elevation for detection
    det = ElevationDetector(topo).withConstantElevation(radians(marconi_min_elevation))

    #continue propagation after logging event
    passes = det.withHandler(ContinueOnEvent())
    
    #detected event/passes
    return passes, topo



#extract interval for aos/los from event detector
def get_pass_intervals(pass_logger):
    """
    Returns intervals of all passes (aos to los) in chronological order
    """
    #get list of all aos/los passings
    events = list(pass_logger.getLoggedEvents())

    #use time since absolute date to order events in chronological order (without this orekit wasn't
    #ordering them the same)
    utc = TimeScalesFactory.getUTC()
    ref = AbsoluteDate(2026, 1, 1, 0, 0, 0.0, utc)
    events.sort(key=lambda e: e.getState().getDate().durationFrom(ref))

    intervals = []
    aos = None

    for ev in events: #go through events in order
        date = ev.getState().getDate() #extract time and state
        
        if ev.isIncreasing(): #AOS, elevation is increasing above threshold
            aos = date #store time
        else: #LOS, elevation is decreasing past threshold
            if aos is not None and date.compareTo(aos) > 0: #los should be after aos
                intervals.append((aos, date)) #store interval
            aos = None #reset next pass

    #retrun list of pass intervals        
    return intervals



def get_max_elevations(max_el_logger, intervals, topo, fixed_frame):
    """
    Returns list of max elevations for each pass in chronological order
    """
    max_events = list(max_el_logger.getLoggedEvents())

    #sort by chronological order
    utc = TimeScalesFactory.getUTC()
    ref = AbsoluteDate(2026, 1, 1, 0, 0, 0.0, utc)
    max_events.sort(key=lambda e: e.getState().getDate().durationFrom(ref))

    max_list = []
    for (aos, los) in intervals:
        best_el = float("nan") #best defaults nan until max found for each pass
        best_az = float("nan")

        for ev in max_events:
            st = ev.getState() #spacecraft state
            date = st.getDate() #date of event

            #for each aos los window
            if date.compareTo(aos) >= 0 and date.compareTo(los) <= 0:
                
                pos_fixed = st.getPVCoordinates(fixed_frame).getPosition() #get spacrcraft position in fixed frame

                elev = degrees(topo.getElevation(pos_fixed, fixed_frame, date)) #get elevation of spacraft
                az = degrees(topo.getAzimuth(pos_fixed, fixed_frame, date)) #get azimuth of spacecraft relative to gs NSWE
                
                if (best_el != best_el) or (elev > best_el):  #if best is nan or elev is larger, keep best
                    best_el = elev
                    best_az = az

        max_list.append({"max_el_deg": best_el, "az_at_max_el": best_az}) #store max elevation and azimuthfor each interval 

    return max_list