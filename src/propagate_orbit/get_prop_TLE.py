"""
 Propagate Orbit

 Description: this script will use take the state vector of SAL-E given by SpaceX prelaunch ODM
 and propagate it forward to when we can expect a pass and return it as a TLE. This TLE can then be 
 given into SatNOGS 

 Inputs: 
 - state vector
 - 

 Outputs:
 - propagated state in TLE format
 - 

"""

#import orekit
import os, sys, string, math
import numpy as np

#import perturbation functions

from J2_force import build_J2_force_model
from drag_force import build_drag_force_model

def build_initial_state(rx,ry,rz,vx,vy,vz,epoch,frame,mass)
    
    return 

