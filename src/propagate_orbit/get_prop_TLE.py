"""
 Propagate Orbit

 Description: this script will use take the state vector of SAL-E given by SpaceX prelaunch ODM
 and propagate it forward to when we can expect a pass and return it as a TLE. The generated TLE 
 will be given to Satnet as an estimate for where to point Marconi antennas during SAL-E's first passes. 

 Inputs: 
 - state vector (ECEF frame from SpaceX)
 - gs location 
 - time of propagation (1 week)


 Outputs:
 - propagated state in TLE format
 - time of each pass after launch (PST)

"""

#initialize
import os, sys, string, math
import numpy as np

#import orekit libraries
import orekit
from orekit.
from orekit.


#import perturbation functions
from j2_model import build_j2_perturbation_model as j2
from drag_model import build_drag_force_model as drag
from satellite_passes import detect_pass, get_pass_intervals

#constants/parameters
area = 0.14 #m2
cd=2.2
mass=2.89 #kg



def pass_TLEs(rx,ry,rz,vx,vy,vz,epoch,frame,mass):

    #define orbit and initial state
    rv = PVcoords
    orbit = CarterianOrbit
    state = SpacecraftState

    #create propegator and add perturbations
    integrator = 
    prop = 

    prop.addForceModel(j2)
    prop.addForceModel(drag)

    #detect and collect pass intervals over the week
    passes = detect_pass()

    log_passes = EventsLogger()
    prop.addEventDetector(log_passes.monitorDetector(passes))
    
    intervals = get_pass_intervals(log_passes)

    #propagate 

    #make TLE templerate

    #convert state to TLEs, append tles for aos/los inside intervals


    return #TLEs and time of each pass after launch





