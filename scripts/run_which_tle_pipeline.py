"""
Combined which_TLE + propagate_orbit pipeline.

1. Run the propagator to produce states.csv (and passes.csv, passes.tle).
2. Run which_TLE match_tle with states_path pointing at that states.csv and consider_states=True.

Run from the repository root so config paths and output files resolve correctly:
    python scripts/run_which_tle_pipeline.py
"""

from pathlib import Path

from src.setup import setup_orekit
setup_orekit()

from configs.config import load_configs
from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import Constants, IERSConventions

from src.propagate_orbit.get_prop_TLE import get_TLEs
from src.which_TLE.pick_TLE import match_tle
from src.helpers.parse_doppler_data import load_doppler_records



def main():
    cfg = load_configs()
    utc = TimeScalesFactory.getUTC()
    ecef = cfg.ecef_frame
    inertial = cfg.inertial_frame
    epoch = cfg.epoch
    muE = Constants.WGS84_EARTH_MU

    Marconi = cfg.stations["Marconi"]
    states_path = "states.csv"
    passes_csv_path = "passes.csv"
    tle_path = "passes.tle"

    get_TLEs(
        position=cfg.position_m,
        velocity=cfg.velocity_mps,
        epoch=epoch,
        inertial_frame=inertial,
        fixed_frame=ecef,
        muE=muE,
        gs_name="Marconi",
        gs_lat=Marconi.lat_deg,
        gs_long=Marconi.lon_deg,
        gs_alt=Marconi.alt_m,
        gs_min_elev=Marconi.min_elevation_deg,
        days=10,
        mass=cfg.mass_kg,
        area=cfg.area_m2,
        cd=cfg.cd,
        csv_path=passes_csv_path,
        tle_path=tle_path,
        state_path=states_path,
    )

    doppler_records = load_doppler_records(cfg.doppler_data_dir, cfg.stations)
    best_tle, ranked = match_tle(
        doppler_records=doppler_records,
        state_weight=1.0,
        consider_states=True,
        states_path=states_path,
        cfg=cfg,
    )
    print("Best TLE:")
    print(best_tle.getLine1())
    print(best_tle.getLine2())
    print("\nRanked (cost ascending):")
    for tle, cost in ranked[:10]:
        print(f"  cost={cost:.2f}  {tle.getLine1()[:22]}...")


if __name__ == "__main__":
    main()
