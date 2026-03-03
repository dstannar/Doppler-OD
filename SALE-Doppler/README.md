# SALE-Doppler: Doppler profile data

Ground-station doppler shift data for SAL-E. One subdirectory per station (e.g. `Marconi/`, `EEDepartment/`); station names must match `configs/stations.yaml`.

## CSV format

- **One file per pass** (recommended): one CSV per pass per station, e.g. `2026-03-29_pass1.csv`.
- **Encoding**: UTF-8.
- **Header row**: required.

### Required columns

| Column     | Type   | Description |
|-----------|--------|-------------|
| `time_utc`| string | UTC time in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.SSSZ` (e.g. `2026-03-29T18:00:00.000Z`). |
| `doppler_hz` | float | Observed one-way doppler shift in Hz. **Sign convention**: positive = satellite approaching the station (range decreasing); negative = receding. |

### Optional columns

| Column          | Type  | Description |
|-----------------|-------|-------------|
| `elevation_deg` | float | Elevation angle of the satellite above the local horizon, in degrees. Used for weighting or filtering low-elevation points. |
| `snr_db`        | float | Signal-to-noise ratio in dB. For future use (e.g. residual weighting). |

### Example (minimal)

```csv
time_utc,doppler_hz
2026-03-29T18:00:00.000Z,-120.5
2026-03-29T18:00:01.000Z,-118.2
2026-03-29T18:00:02.000Z,-115.1
```

### Example (with optional columns)

```csv
time_utc,doppler_hz,elevation_deg,snr_db
2026-03-29T18:00:00.000Z,-120.5,12.3,8.5
2026-03-29T18:00:01.000Z,-118.2,14.1,9.0
```

The files in `Marconi/` and `EEDepartment/` are example passes with this format.
