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
from setup import setup_orekit
setup_orekit()
from math import radians

#import orekit libraries
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint
from org.orekit.propagation.events import ElevationDetector
from org.orekit.frames import TopocentricFrame
from org.orekit.propagation.events.handlers import ContinueOnEvent
from org.orekit.utils import Constants

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
    return passes



#extract interval for aos/los from event detector
def get_pass_intervals(pass_logger):
    
    #use EventLogger to extraxt time intervals for aos/los as list
    events=list(pass_logger.getLoggedEvents())
    events.sort(key=lambda e: e.getState().getDate()) #chronological order

    #store all passes
    intervals = []
    aos = None
    for ev in events: #go through events in order
        date = ev.getState().getDate() #extract time

        if ev.isIncreasing(): #AOS, eleveation is increasing above threshold
            aos = date #store this time
        else: #LOS, if decreasing past threshold
            if aos is not None and date.compareTo(aos) > 0: #run after an AOS
                intervals.append((aos, date)) #store interval
            aos = None #reset next pass

    #return list of intervals 
    return intervals 