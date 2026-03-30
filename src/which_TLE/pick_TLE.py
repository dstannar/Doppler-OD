"""Pick the candidate TLE that best matches Doppler (and optionally state)."""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np

from src.helpers.parse_doppler_data import load_doppler_records
from src.which_TLE.get_TLEs import get_candidate_tles
from src.which_TLE.doppler_from_TLE import predict_doppler
from src.which_TLE.batch_ls_TLE import combined_cost
from src.helpers.state_from_TLE import state_from_TLE
from configs.config import load_configs

from org.orekit.frames import FramesFactory, ITRFVersion
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import IERSConventions, PVCoordinates
from org.hipparchus.geometry.euclidean.threed import Vector3D


def _doppler_records_for_predict(doppler_raw):
    """
    Convert doppler array to list of dicts for predict_doppler.

    Each dict has keys station_id, time_utc, doppler_hz so that
    rec['time_utc'] and rec['station_id'] work in predict_doppler.
    """
    out = []
    for row in doppler_raw:
        if hasattr(row, "keys"):
            out.append({"station_id": row["station_id"], "time_utc": row["time_utc"], "doppler_hz": row["doppler_hz"]})
        else:
            out.append({"station_id": row[0], "time_utc": row[1], "doppler_hz": row[2]})
    return out


def _state_at_epoch(states_list, epoch_utc):
    """
    Return the state dict from states_list whose epoch is closest to epoch_utc.
    """
    if not states_list or epoch_utc is None:
        return None
    try:
        t_ref = datetime.fromisoformat(epoch_utc.replace("Z", "+00:00"))
    except Exception:
        return None
    best = None
    best_dt_sec = None
    for s in states_list:
        try:
            t = datetime.fromisoformat(s["epoch"].replace("Z", "+00:00"))
        except Exception:
            continue
        dt_sec = abs((t - t_ref).total_seconds())
        if best_dt_sec is None or dt_sec < best_dt_sec:
            best_dt_sec = dt_sec
            best = s
    return best


def load_states(states_path):
    """
    Load state history from CSV (states.csv from propagator).

    CSV must have: Date (UTC), Rx (m), Ry (m), Rz (m), Vx (m/s), Vy (m/s), Vz (m/s).
    States are in ECEF.

    Parameters
    ----------
    states_path : str or Path
        Path to CSV file.

    Returns
    -------
    list of dict
        Each dict: epoch (str ISO-8601), position_m (3), velocity_mps (3).
    """
    path = Path(states_path)
    if not path.exists():
        raise FileNotFoundError(f"States file not found: {path}")

    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = (row.get("Date (UTC)") or "").strip()
            if not t:
                raise ValueError("Date (UTC) is not in csv")
            try:
                rx, ry, rz = float(row["Rx (m)"]), float(row["Ry (m)"]), float(row["Rz (m)"])
                vx, vy, vz = float(row["Vx (m/s)"]), float(row["Vy (m/s)"]), float(row["Vz (m/s)"])
            except (KeyError, ValueError):
                raise ValueError("Rx (m), Ry (m), Rz (m), Vx (m/s), Vy (m/s), Vz (m/s) are not in csv")
            rows.append({
                "epoch": t,
                "position_m": np.array([rx, ry, rz]),
                "velocity_mps": np.array([vx, vy, vz]),
            })
    return rows


def _tle_state_in_ecef(tle, epoch_str, ecef_frame):
    """
    Get TLE state at epoch and transform from TEME (TLE frame) to ECEF.

    state_from_TLE returns state in TEME, csv is in ecef
    """

    pos_teme, vel_teme = state_from_TLE(tle, epoch_str)
    utc = TimeScalesFactory.getUTC()
    absolute_date = AbsoluteDate(epoch_str, utc)
    teme = FramesFactory.getTEME()
    pv_teme = PVCoordinates(
        Vector3D(float(pos_teme[0]), float(pos_teme[1]), float(pos_teme[2])),
        Vector3D(float(vel_teme[0]), float(vel_teme[1]), float(vel_teme[2])),
    )
    transform = teme.getTransformTo(ecef_frame, absolute_date)
    pv_ecef = transform.transformPVCoordinates(pv_teme)
    p = pv_ecef.getPosition()
    v = pv_ecef.getVelocity()
    pos_ecef = np.array([p.getX(), p.getY(), p.getZ()], dtype=float)
    vel_ecef = np.array([v.getX(), v.getY(), v.getZ()], dtype=float)
    return pos_ecef, vel_ecef



def match_tle(
    doppler_records,
    cfg,
    state=None,
    state_weight=1.0,
    states_path="states.csv",
    consider_states=True,
    candidates=None,
):
    """
    Find the Space-Track TLE that best matches doppler (and optionally state).

    Parameters
    ----------
    doppler_records : array
        (n, 3) array with columns [station_id, time_utc, doppler_hz].
    state : dict, optional
        If consider_states and state is provided, use this state (epoch,
        position_m, velocity_mps in ECEF). Otherwise state is loaded from
        states_path and the row closest to cfg.epoch_utc is used.
    state_weight : float
        Weight for state term in combined cost when consider_states is True.
    consider_states : bool
        If True, load state (from states_path or state), transform TLE state
        TEME->ECEF, and include state term in cost. If False, do not consider
        states in the batch LS (doppler-only).
    states_path : str or Path
        Path to states CSV (Date (UTC), Rx, Ry, Rz, Vx, Vy, Vz in ECEF). Used
        when consider_states is True and state is None.
    cfg : SimpleNamespace
        Mission config loaded by the caller.

    Returns
    -------
    best_tle
        The TLE with minimum combined cost.
    ranked : list of (tle, cost)
        All candidates sorted by cost ascending, for diagnostics.
    """
    if doppler_records is None:
        doppler_raw = load_doppler_records(cfg.doppler_data_dir, cfg.stations)
    else:
        # Accept (n,3) arrays, lists of tuples, or lists of dicts.
        if len(doppler_records) > 0 and hasattr(doppler_records[0], "keys"):
            doppler_raw = np.asarray(
                [(r["station_id"], r["time_utc"], r["doppler_hz"]) for r in doppler_records],
                dtype=object,
            )
        else:
            doppler_raw = np.asarray(doppler_records)
        if doppler_raw.ndim == 1:
            doppler_raw = np.column_stack(
                [[r[0] for r in doppler_raw], [r[1] for r in doppler_raw], [r[2] for r in doppler_raw]]
            )
    doppler_for_predict = _doppler_records_for_predict(doppler_raw)

    freq_tx_hz = cfg.frequency_hz
    stations_config = cfg.stations

    if candidates is None:
        candidates = get_candidate_tles(cfg)
    if not candidates:
        raise RuntimeError("No candidate TLEs returned from get_candidate_tles.")

    frame = cfg.ecef_frame
    state_obs = None
    state_epoch_str = None
    if consider_states:
        if state is not None:
            state_obs = np.concatenate([
                np.asarray(state["position_m"]),
                np.asarray(state["velocity_mps"]),
            ])
            state_epoch_str = state.get("epoch")
        else:
            states_list = load_states(states_path)
            epoch_utc = getattr(cfg, "epoch_utc", None)
            state_dict = _state_at_epoch(states_list, epoch_utc)
            if state_dict is not None:
                state_obs = np.concatenate([
                    state_dict["position_m"],
                    state_dict["velocity_mps"],
                ])
                state_epoch_str = state_dict["epoch"]

    ranked = []
    for tle in candidates:
        pred_hz = predict_doppler(tle, doppler_for_predict, stations_config, frame, freq_tx_hz)
        state_tle = None
        if consider_states and state_obs is not None and state_epoch_str:
            pos_ecef, vel_ecef = _tle_state_in_ecef(tle, state_epoch_str, frame)
            state_tle = np.concatenate([pos_ecef, vel_ecef])
        cost = combined_cost(
            doppler_raw,
            pred_hz,
            state_obs=state_obs,
            state_tle=state_tle,
            state_weight=state_weight if consider_states else 0.0,
        )
        ranked.append((tle, cost))

    ranked.sort(key=lambda x: x[1])
    best_tle = ranked[0][0]
    return best_tle, ranked


# Set to False to run doppler-only (don't consider states in batch LS).
CONSIDER_STATES = False
