"""
Load and expose mission and station configuration.

- Load SALE.yaml (configs/SALE.yaml) and
  expose launch_date, launch_site, doppler_data_dir, orekit_data_path,
  space_weather_file, and any other fields needed by which_TLE.
- Load stations.yaml and expose stations with lat_deg, lon_deg, alt_m, min_elevation_deg.
- Provide a single place for config paths and parsed structures so the rest of
  the library does not duplicate YAML loading.
"""
