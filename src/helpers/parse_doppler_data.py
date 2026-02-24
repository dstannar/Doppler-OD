"""
parse_doppler_data.py
Load and validate doppler profile CSV data.

- Load doppler CSV(s) from the doppler_data_dir and station subdirs
  (SALE-Doppler/Marconi/, SALE-Doppler/EEDepartment/).
- Parse into a common structure: observation times, station name,
  doppler_hzs.
- Validate station names against config (stations.yaml). Support one file per
  pass per station.
- Document and enforce the CSV format (columns, units, sign convention:
  positive doppler = satellite approaching the station).
"""
