"""
 Propagate Orbit

 Description: this script will use take the state vector of SAL-E given by SpaceX prelaunch ODM
 and propagate it forward to when we can expect a pass and return it as a TLE. This TLE can then be 
 given into Satnet 

 Inputs: 
 - state vector (ECEF frame from SpaceX)
 - only calculate TLE when satellite inclination/position is within inclination of marconi


 Outputs:
 - propagated state in TLE format
 - 

"""

#initialize
import os, sys, string, math
import numpy as np

#import orekit libraries

#import perturbation functions
from propagate_orbit.j2_model import build_j2_perturbation_model
from propagate_orbit.drag_model import build_drag_force_model

#constants/parameters
area = 0.14 #m2
cd=2.2
mass=2.89 #kg


def build_initial_state(rx,ry,rz,vx,vy,vz,epoch,frame,mass):

    
    return 


rv = build_initial_state(0,0,0,0,0,0,'2024-06-01T00:00:00.000Z','ECEF',mass)
prop = 



