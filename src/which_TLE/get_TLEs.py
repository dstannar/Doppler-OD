"""
get_TLEs.py
Space-Track TLE retrieval with caching and rate limiting.

- READ SPACE-TRACK API RULES BEFORE WRITING THIS
- Fetch TLEs from Space-Track filtered by launch_date and launch_site (from
  config) so we get only the subset from the same launch (e.g. Transporter 16).
- Use a single bulk request, do not issue per-TLE API calls.
- Cache responses for at least a few hours. Use cached TLEs until time expires.
"""


def fetch_tles(launch_date, launch_site, cache_dir=None, cache_hours=6):
    """
    Single bulk Space-Track request filtered by launch_date and launch_site.

    Respect API rate limits. use cached TLEs
    until cache_hours expire. Do not issue per-TLE API calls.

    Parameters
    ----------
    launch_date : str
        Launch date filter (e.g. "2026-03-29").
    launch_site : str
        Launch site code filter (e.g. "AFWTR").
    cache_dir : path-like, optional
        Directory for cache file; if None, no disk cache.
    cache_hours : float
        Cache TTL in hours.

    Returns
    -------
    list
        List of TLE objects
    """