# state_from_TLE.py
from org.orekit.propagation.analytical.tle import TLEPropagator
from org.orekit.time import AbsoluteDate
from org.orekit.time import TimeScalesFactory


def state_from_TLE(tle, epoch):
    """
    Compute TLE state (position and velocity) at a given epoch.

    Parameters
    ----------
    tle : org.orekit.propagation.analytical.tle.TLE
        Orekit TLE object.
    epoch : org.orekit.time.AbsoluteDate or str
        Target epoch of type ISO-8601 like "2026-03-03T12:34:56.000" (UTC) or org.orekit.time.AbsoluteDate

    Returns
    -------
    (pos_m, vel_mps) : ((x,y,z), (vx,vy,vz))
        Position in meters and velocity in meters/second, expressed in the
        propagator's frame (the frame used by the TLE propagator).
    """
    # TLE propagator
    propagator = TLEPropagator.selectExtrapolator(tle)

    # check epoch input
    if isinstance(epoch, AbsoluteDate):
        target_date = epoch
    elif isinstance(epoch, str):
        utc = TimeScalesFactory.getUTC()
        target_date = AbsoluteDate(epoch, utc)
    else:
        raise TypeError(f"epoch must be an Orekit AbsoluteDate or ISO-8601 str")

    # Propagate to the target epoch and get PV in the propagator's frame.
    # Using `propagate` avoids issues with certain JPype overload bindings for
    # `getPVCoordinates(date, frame)` that can surface as a `'super' object`
    # AttributeError in some environments.
    state = propagator.propagate(target_date)
    pv = state.getPVCoordinates()
    p = pv.getPosition()
    v = pv.getVelocity()

    pos_m = (float(p.getX()), float(p.getY()), float(p.getZ()))
    vel_mps = (float(v.getX()), float(v.getY()), float(v.getZ()))

    return pos_m, vel_mps