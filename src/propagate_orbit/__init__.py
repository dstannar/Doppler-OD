"""
propagate_orbit will propagate the state vector of SAL-E given by SpaceX prelaunch ODM and return
a TLE of SAL-E at an epoch when it will enter Marconi's line of sight inlcination. This propgation
will account for only the J2 and atmospheric drag perturbations that SAL-E will experience after 
being deployed at an altitude of 510km (LEO). Because we only need to predict SAL-E location for about a 
week until SpaceTrack TLE's are available, an estimation using these two pertubrations should
be sufficient.

This folder contains a drag model function, a J2 perturbation function, and a main function that will
take the state vector, propagate it with perturbations to a epoch where a pass begins, and return 
TLEs of every pass. 

"""