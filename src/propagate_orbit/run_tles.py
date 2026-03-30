"""Dev script: run propagator for SALE and plot ground track."""

import csv
import math
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np

from src.setup import setup_orekit

setup_orekit("SALE.yaml")

from org.orekit.utils import Constants
from configs.config import load_configs
from src.propagate_orbit.get_prop_TLE import get_TLEs

cfg = load_configs("SALE.yaml")
launch_date = cfg.launch_date
launch_site = cfg.launch_site
doppler_data_dir = cfg.doppler_data_dir
orekit_data_path = cfg.orekit_data_path
space_weather_file = cfg.space_weather_file
epoch_utc = cfg.epoch_utc
epoch = cfg.epoch
position_m = cfg.position_m
velocity_mps = cfg.velocity_mps
area_m2 = cfg.area_m2
cd = cfg.cd
mass_kg = cfg.mass_kg
stations = cfg.stations

ecef = cfg.ecef_frame
inertial = cfg.inertial_frame
muE = Constants.WGS84_EARTH_MU

#define Marconi station params
Marconi = stations["Marconi"]
Marconi_lat = Marconi.lat_deg
Marconi_lon = Marconi.lon_deg
Marconi_alt = Marconi.alt_m
marconi_min_elevation = Marconi.min_elevation_deg


def _ecef_to_geodetic_deg(x_m, y_m, z_m):
    """
    Convert WGS84 ECEF coordinates to geodetic latitude/longitude (degrees).
    Uses Bowring's closed-form approximation, which is accurate for plotting.
    """
    a = 6378137.0
    f = 1.0 / 298.257223563
    b = a * (1.0 - f)
    e2 = f * (2.0 - f)
    ep2 = (a * a - b * b) / (b * b)

    lon = math.atan2(y_m, x_m)
    p = math.hypot(x_m, y_m)
    theta = math.atan2(z_m * a, p * b)
    sin_t = math.sin(theta)
    cos_t = math.cos(theta)
    lat = math.atan2(
        z_m + ep2 * b * sin_t * sin_t * sin_t,
        p - e2 * a * cos_t * cos_t * cos_t,
    )

    return math.degrees(lat), math.degrees(lon)


def _insert_dateline_breaks(lons_deg, lats_deg):
    """
    Insert NaNs where longitude jumps across the dateline so lines do not wrap.
    """
    out_lons = []
    out_lats = []
    prev_lon = None
    for lon, lat in zip(lons_deg, lats_deg):
        if prev_lon is not None and abs(lon - prev_lon) > 180.0:
            out_lons.append(np.nan)
            out_lats.append(np.nan)
        out_lons.append(lon)
        out_lats.append(lat)
        prev_lon = lon
    return np.array(out_lons), np.array(out_lats)


def _parse_iso_utc(ts_text):
    """Parse UTC timestamp formatted like 2026-03-29T20:56:11.063."""
    return datetime.fromisoformat(ts_text)


def _to_pdt(dt_utc):
    """Convert UTC datetime to fixed PDT (UTC-7) for plot labels."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    pdt = timezone(timedelta(hours=-7), name="PDT")
    return dt_utc.astimezone(pdt)


def _try_get_earth_overlay():
    """
    Return an equirectangular Earth image array for map background if available.
    Falls back to None if download is unavailable.
    """
    # Public domain monthly Earth topography map (equirectangular).
    url = "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.jpg"
    try:
        with urlopen(url, timeout=8) as resp:
            data = resp.read()
        return plt.imread(BytesIO(data), format="jpg")
    except Exception:
        return None


def plot_ground_track(states_csv_path, passes_csv_path, deploy_time_utc, gs_lat_deg, gs_lon_deg, out_path="ground_track.png"):
    """
    Build and save a ground track plot from `states.csv`, mark ground station,
    and display the figure.
    """
    states_csv_path = Path(states_csv_path)
    passes_csv_path = Path(passes_csv_path)

    # Read first two pass windows and estimate max-elevation time at pass midpoint.
    pass_windows = []
    with passes_csv_path.open("r", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if len(pass_windows) >= 2:
                break
            aos = _parse_iso_utc(row["AOS (UTC)"])
            los = _parse_iso_utc(row["LOS (UTC)"])
            t_max = aos + (los - aos) / 2
            pass_windows.append({"aos": aos, "los": los, "t_max": t_max})

    if len(pass_windows) < 2:
        raise ValueError(f"Need at least two passes in {passes_csv_path}")

    # Gather geodetic points from deploy epoch through slightly after pass 2 LOS.
    t_start = _parse_iso_utc(deploy_time_utc.replace("Z", ""))
    t_end = pass_windows[1]["los"] + (pass_windows[1]["los"] - pass_windows[1]["aos"]) * 0.05
    track_between = []  # list of (time, lat, lon)
    tracks = [[], []]   # pass-only segments for annotation markers

    with states_csv_path.open("r", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            t_utc = _parse_iso_utc(row["Date (UTC)"])
            x = float(row["Rx (m)"])
            y = float(row["Ry (m)"])
            z = float(row["Rz (m)"])
            lat_deg, lon_deg = _ecef_to_geodetic_deg(x, y, z)
            if t_start <= t_utc <= t_end:
                track_between.append((t_utc, lat_deg, lon_deg))

            for i, w in enumerate(pass_windows):
                if w["aos"] <= t_utc <= w["los"]:
                    tracks[i].append((t_utc, lat_deg, lon_deg))

    if not track_between:
        raise ValueError("Could not find state samples between deploy epoch and pass 2.")
    if not tracks[0] or not tracks[1]:
        raise ValueError("Could not find state samples for first two pass windows.")

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#f4f6f8")
    ax.set_title("SAL-E Ground Track Post TR16 Deployment", fontsize=15, weight="bold", pad=12)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.set_facecolor("#cfe8ff")
    ax.grid(True, alpha=0.30, linestyle="--", linewidth=0.7, color="#355070")
    ax.set_xticks(np.arange(-180, 181, 30))
    ax.set_yticks(np.arange(-90, 91, 15))
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color("#2f3e46")

    earth_img = _try_get_earth_overlay()
    if earth_img is not None:
        ax.imshow(
            earth_img,
            extent=(-180, 180, -90, 90),
            origin="upper",
            aspect="auto",
            alpha=0.82,
            zorder=0,
        )

    # Plot full segment between deploy and just after pass 2 LOS.
    lons_between = [p[2] for p in track_between]
    lats_between = [p[1] for p in track_between]
    lons_plot, lats_plot = _insert_dateline_breaks(lons_between, lats_between)
    ax.plot(
        lons_plot,
        lats_plot,
        color="#1d4ed8",
        linewidth=2.1,
        label="Ground Track (Deploy -> Pass 2)",
        zorder=3,
    )

    colors = ["tab:orange", "tab:purple"]

    # Mark deploy point (first sample in deploy->P2 window, i.e., epoch sample).
    deploy_time = track_between[0][0]
    deploy_lat = track_between[0][1]
    deploy_lon = track_between[0][2]
    ax.scatter([deploy_lon], [deploy_lat], color="#16a34a", s=80, marker="o", zorder=6)
    deploy_time_pdt = _to_pdt(deploy_time)
    ax.text(
        deploy_lon + 2.0,
        deploy_lat + 1.5,
        f"Deploy {deploy_time_pdt.strftime('%Y-%m-%d %H:%M:%S PDT')}",
        color="#166534",
        fontsize=9,
        weight="bold",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", boxstyle="round,pad=0.2"),
    )

    # Mark approximate max-elevation location/time for pass 1 and 2.
    for idx, track in enumerate(tracks, start=1):
        t_target = pass_windows[idx - 1]["t_max"]
        nearest = min(track, key=lambda p: abs((p[0] - t_target).total_seconds()))
        t_label = _to_pdt(nearest[0]).strftime("%Y-%m-%d %H:%M:%S PDT")
        lat_max = nearest[1]
        lon_max = nearest[2]
        ax.scatter([lon_max], [lat_max], color=colors[idx - 1], s=70, marker="x", linewidths=2.0, zorder=7)
        ax.text(
            lon_max + 2.0,
            lat_max - 2.0,
            f"Pass {idx} max ~ {t_label}",
            color=colors[idx - 1],
            fontsize=8,
            bbox=dict(facecolor="white", alpha=0.65, edgecolor="none", boxstyle="round,pad=0.2"),
        )

    ax.scatter([gs_lon_deg], [gs_lat_deg], color="#b91c1c", s=90, marker="^", label="Marconi GS", zorder=5)
    ax.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#94a3b8")

    out_path = Path(out_path)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    print(f"Saved ground track figure to {out_path.resolve()}")
    plt.show()


passes_csv, tle_path_out, states_csv = get_TLEs(
    position=position_m,
    velocity =velocity_mps,
    epoch=epoch,
    inertial_frame=inertial, 
    fixed_frame=ecef,
    muE=muE,
    gs_name="Marconi",
    gs_lat=Marconi_lat,
    gs_long=Marconi_lon,
    gs_alt=Marconi_alt,
    gs_min_elev=marconi_min_elevation,
    days=10,
    mass = mass_kg,
    area=area_m2, 
    cd=cd,
    space_weather_file=space_weather_file,
    csv_path = "passes.csv",
    tle_path = "passes.tle",
    state_path = "states.csv"
    
             )

plot_ground_track(states_csv, passes_csv, epoch_utc, Marconi_lat, Marconi_lon, out_path="ground_track.png")














