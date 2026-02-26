"""
state_from_TLE.py
Compute TLE state (position and velocity) at a given epoch.

- Given a TLE and an epoch (e.g. from the optional propagator state), propagate
  the TLE with Orekit to that epoch and return position (m) and velocity (m/s)
  in the SAME FRAME as the propagator state 
"""
def state_from_TLE(tle, epoch):
  """
  Compute TLE state (position and velocity) at a given epoch.

  Parameters
  ----------
  tle : TLE
  epoch : Orekit AbsoluteDate or ISO str
  """
  return #position and velocity in the same frame as the tle state 