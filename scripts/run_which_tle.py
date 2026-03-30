"""Run the which_TLE pipeline (best Space-Track TLE vs Doppler) and plot CSV vs TLE Doppler."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.paths import repo_root
from src.setup import setup_orekit

MISSION = "SALE.yaml"
STATES = "states.csv"
OUT = None
SHOW_PLOT = True
CONSIDER_STATES = True

setup_orekit(MISSION)

from configs.config import load_configs
from src.helpers.parse_doppler_data import load_doppler_records
from src.which_TLE.doppler_from_TLE import predict_doppler
from src.which_TLE.pick_TLE import match_tle


def _doppler_records_for_predict(doppler_raw):
    """Match pick_TLE: list of dicts for predict_doppler."""
    out = []
    for row in doppler_raw:
        out.append(
            {
                "station_id": row[0],
                "time_utc": row[1],
                "doppler_hz": row[2],
            }
        )
    return out


def main():
    root = repo_root()
    states_path = Path(STATES)
    if not states_path.is_absolute():
        states_path = root / states_path

    cfg = load_configs(MISSION)
    doppler_raw = load_doppler_records(cfg.doppler_data_dir, cfg.stations)

    best_tle, ranked = match_tle(
        doppler_raw,
        cfg,
        states_path=states_path,
        consider_states=CONSIDER_STATES,
    )

    doppler_for_predict = _doppler_records_for_predict(doppler_raw)
    pred_hz = np.asarray(
        predict_doppler(best_tle, doppler_for_predict, cfg.stations, cfg.ecef_frame, cfg.frequency_hz),
        dtype=float,
    )

    norad = int(best_tle.getSatelliteNumber())
    print(f"Best TLE NORAD ID: {norad}")
    print(f"Best cost: {ranked[0][1]:.6g}")
    print("Ranked candidates (up to 15):")
    for i, (tle, cost) in enumerate(ranked[:15]):
        print(f"  {i + 1}. NORAD {int(tle.getSatelliteNumber())}  cost={cost:.6g}")

    seen = set()
    station_order = []
    for sid in doppler_raw[:, 0]:
        if sid not in seen:
            seen.add(sid)
            station_order.append(sid)

    n = len(station_order)
    fig, axes = plt.subplots(n, 1, figsize=(12, max(4.0, 3.5 * n)), sharex=False)
    axes = np.atleast_1d(axes).ravel()

    for ax, sid in zip(axes, station_order):
        mask = doppler_raw[:, 0] == sid
        t = np.asarray(doppler_raw[mask, 1])
        obs = np.asarray(doppler_raw[mask, 2], dtype=float)
        pred = pred_hz[mask]

        ax.plot(t, obs, "o", ms=3, alpha=0.75, label="CSV (observed)")
        ax.plot(t, pred, "-", lw=1.6, label="TLE predicted")
        ax.set_ylabel("Doppler (Hz)")
        ax.set_title(str(sid))
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.35)

    fig.suptitle(f"Observed vs TLE Doppler — best NORAD {norad}", fontsize=12, y=1.02)
    fig.tight_layout()

    if OUT:
        out_path = Path(OUT)
        if not out_path.is_absolute():
            out_path = root / out_path
        fig.savefig(out_path, dpi=160, bbox_inches="tight")
        print(f"Saved figure to {out_path.resolve()}")

    if SHOW_PLOT:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
