# state_from_TLE.py
"""
Compute TLE state (position and velocity) at a given epoch.

- Given a TLE and an epoch, propagate the TLE with Orekit to that epoch and
  return position (m) and velocity (m/s) in the SAME FRAME as the TLE propagator state.
"""

from typing import Tuple, Union

from org.orekit.propagation.analytical.tle import TLEPropagator
from org.orekit.time import AbsoluteDate
from org.orekit.time import TimeScalesFactory


def state_from_TLE(tle, epoch: Union[AbsoluteDate, str]) -> Tuple[Tuple[float, float, float],
                                                                  Tuple[float, float, float]]:
    """
    Compute TLE state (position and velocity) at a given epoch.

    Parameters
    ----------
    tle : org.orekit.propagation.analytical.tle.TLE
        Orekit TLE object.
    epoch : org.orekit.time.AbsoluteDate or str
        Target epoch. If str, should be an Orekit-parsable date-time string,
        commonly ISO-8601 like "2026-03-03T12:34:56.000" (UTC).

    Returns
    -------
    (pos_m, vel_mps) : ((x,y,z), (vx,vy,vz))
        Position in meters and velocity in meters/second, expressed in the
        propagator's frame (the frame used by the TLE propagator).
    """
    # TLE propagator
    propagator = TLEPropagator.selectExtrapolator(tle)

    # Normalize epoch input
    if isinstance(epoch, AbsoluteDate):
        target_date = epoch
    elif isinstance(epoch, str):
        utc = TimeScalesFactory.getUTC()
        # Orekit AbsoluteDate(String, TimeScale) 
        target_date = AbsoluteDate(epoch, utc)
    else:
        raise TypeError(f"epoch must be an Orekit AbsoluteDate or ISO str, got {type(epoch)}")

    # Use the propagator's frame (same frame as the TLE state)
    frame = propagator.getFrame()

    # Get PV at target epoch in that frame
    pv = propagator.getPVCoordinates(target_date, frame)
    p = pv.getPosition()
    v = pv.getVelocity()

    pos_m = (float(p.getX()), float(p.getY()), float(p.getZ()))
    vel_mps = (float(v.getX()), float(v.getY()), float(v.getZ()))

    return pos_m, vel_mps