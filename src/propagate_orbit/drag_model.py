"""LEO drag: NRLMSISE00 + CSSI space weather."""

from org.orekit.forces.drag import DragForce, IsotropicDrag
from org.orekit.utils import Constants
from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory
from org.orekit.models.earth.atmosphere import NRLMSISE00
from org.orekit.models.earth.atmosphere.data import CssiSpaceWeatherData
from org.orekit.data import DataSource
from org.orekit.time import TimeScalesFactory
 
#drag force function
def build_drag_force_model(frame, area, drag_coef, space_weather_file, atmosphere=None):
     #If atmosphere is None:
     #builds Earth ellipsoid (WGS84) in the provided Earth-fixed frame
     #inputs CSSI space weather data
     #builds NRLMISE-00 atmosphere model
    if atmosphere is None:
        earth = OneAxisEllipsoid(
            Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
            Constants.WGS84_EARTH_FLATTENING,
            frame
        )
        
        utc = TimeScalesFactory.getUTC()

        ds = DataSource(space_weather_file)
        sw = CssiSpaceWeatherData(ds, utc)  
        sun = CelestialBodyFactory.getSun()
        atmosphere = NRLMSISE00(sw,sun,earth,utc)
       
        #drag perturbation force model
        return DragForce(atmosphere, IsotropicDrag(area, drag_coef))
 
   
 