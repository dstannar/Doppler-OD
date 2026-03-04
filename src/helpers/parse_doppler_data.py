"""
parse_doppler_data.py
Load and validate doppler profile CSV data.

- Load doppler CSV(s) from the doppler_data_dir and station subdirs
  (SALE-Doppler/Marconi/, SALE-Doppler/EEDepartment/).
- Parse into a flat list of records (time_utc, station_id, doppler_hz) for
  use by which_TLE and doppler_OD.
- Validate station names against config (stations.yaml). Support one file per
  pass per station.
- Document and enforce the CSV format (columns, units, sign convention:
  positive doppler = satellite approaching the station).
"""

import csv
from pathlib import Path

import numpy as np


def _get_csv_files(root: Path):
    """get all CSV files under root"""
    return sorted(root.rglob("*.csv"))


def load_doppler_records(doppler_data_dir, stations_config):
    """
    Load Doppler CSV(s) from directory and station subdirs; return flat records.

    Scan doppler_data_dir and station subdirs; parse CSVs into a common
    numpy structured array.

    Parameters
    ----------
    doppler_data_dir : path
        Root path (e.g. SALE-Doppler); subdirs per station.
    stations_config : dict
        Station names

    Returns
    -------
    numpy.ndarray
        Structured array with fields:

        - station_id : str
        - time_utc : numpy.datetime64[ms]
        - doppler_hz : float
    """
    root = Path(doppler_data_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Doppler data directory does not exist: {root}")

    station_names = stations_config.keys()

    csv_files = _get_csv_files(root)
    if not csv_files:
        raise ValueError(f"No CSV files found under doppler_data_dir: {root}")

    records = []

    for csv_path in csv_files:
        parent_name = csv_path.parent.name
        if parent_name in station_names:
            station_id = parent_name
        else:
            raise ValueError(f"Station {parent_name} not found in stations_config")

        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                raise ValueError(f"CSV file has no header row: {csv_path}")

            fieldnames = [name.strip() for name in reader.fieldnames]
            required = {"time_utc", "doppler_hz"}
            missing = required - fieldnames
            if missing:
                raise ValueError(f"CSV {csv_path} is missing required columns: {sorted(missing)}")


            for row_idx, row in enumerate(reader):
                time_str = (row.get("time_utc")).strip()
                doppler_str = (row.get("doppler_hz")).strip()

                if not time_str or not doppler_str:
                    raise ValueError(f"Missing time_utc or doppler_hz in {csv_path} at row {row_idx}")

                try:
                    time_utc = np.datetime64(time_str)
                except Exception:
                    raise ValueError(f"Invalid time_utc '{time_str}' in {csv_path} at row {row_idx}")

                try:
                    doppler_hz = float(doppler_str)
                except Exception:
                    raise ValueError(f"Invalid doppler_hz '{doppler_str}' in {csv_path} at row {row_idx}")


                records.append(
                    (station_id, time_utc, doppler_hz)
                )

    return np.asarray(records)