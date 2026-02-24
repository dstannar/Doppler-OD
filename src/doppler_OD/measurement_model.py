"""
Convert doppler observations into Orekit measurements for BatchLSEstimator.

- Take the loaded doppler data (time_utc, station_id, doppler_hz and ground-station definitions from config.
- Build Orekit ObservedMeasurement instances for range-rate Convert doppler Hz to range rate; 
- Register each measurement with its time and station so Orekit's
  BatchLSEstimator can compute predicted values and partials internally (STM
  and measurement sensitivity are handled by Orekit).
"""
