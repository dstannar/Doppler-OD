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


#import orekit libraries


#build ground station and event detector for satellite passes 
def detect_pass(name, latitude, longtiude, altitude, marconi_min_elevation):

    #see GeodeticPoint to define ground station location point

    #use orekit TopocentricFrame to define ground station frame

    #use orekit ElevationDetector.withConstantElevation to set up minimum elevation for detection

    return #detected event/pass



#extract interval for aos/los from event detector
def get_pass_intervals(event_logger)
    
    #use EventLogger to extraxt time intervals for aos/los

    return #intervals 