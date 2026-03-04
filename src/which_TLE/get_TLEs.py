"""
get_TLEs.py
Space-Track TLE retrieval with caching and rate limiting.

- Fetch TLEs from Space-Track filtered by launch_date and launch_site (from
  config) so we get only the subset from the same launch (e.g. Transporter 16).
- Use a single bulk request, do not issue per-TLE API calls.
- Cache responses for at least a few hours. Use cached TLEs until time expires.
"""

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_CACHE_HOURS = 2.0  # GP (aka TLEs) guideline: max 1 request per hour

_RATE_STATE_FILE = Path.home() / ".spacetrack_rate_state.json"

from configs.config import load_configs
cfg = load_configs()
launch_date = cfg.launch_date
launch_site = cfg.launch_site
cache_dir = cfg.cache_dir


def _load_rate_state():
    """Load last GP query time from rate state file"""

    if not _RATE_STATE_FILE.exists():
        return None

    raw = json.loads(_RATE_STATE_FILE.read_text(encoding="utf-8"))
    ts = raw.get("last_gp_query_utc")
    
    if not ts:
        return None
    
    dt = datetime.fromisoformat(ts)

    return dt


def _save_rate_state(last_gp_query_utc):
    """Write last GP query time to rate state file."""
    log_item = {}
    if last_gp_query_utc is not None:
        log_item["last_gp_query_utc"] = last_gp_query_utc.isoformat()
    
    try:
        _RATE_STATE_FILE.write_text(json.dumps(log_item), encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to save rate state to {_RATE_STATE_FILE}: {e}")


def _cache_file(launch_date, launch_site, cache_dir):
    root = cache_dir
    root.mkdir(parents=True, exist_ok=True)
    safe_date = launch_date.replace("/", "-")
    safe_site = launch_site.replace("/", "-")
    return root / f"tles_gp_{safe_date}_{safe_site}.tle"


def _load_cached_tles(cache_path, cache_hours):
    if not cache_path.exists():
        return None

    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)

    now = datetime.now(timezone.utc)
    age_hours = (now - mtime).total_seconds() / 3600.0
    if age_hours > cache_hours:
        return None

    text = cache_path.read_text(encoding="utf-8")

    lines = [ln for ln in text.splitlines()]

    return lines


def _save_cached_tles(cache_path, lines):
    text = "\n".join(lines) + "\n"
    try:
        cache_path.write_text(text, encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to save cached TLEs to {cache_path}: {e}") from e


def _build_gp_query_url(launch_date, launch_site):
    """
    Build Space-Track GP query URL for TLEs filtered by launch date and site.

    The query:
    - Restricts to objects from the specified launch (LAUNCH_DATE and SITE)
    - Restricts to on-orbit objects (DECAY_DATE/null-val)
    - Uses EPOCH/>now-10 to get the newest propagable set from the last 10 days
    - Requests standard TLE format (format/tle)
    """
    base = "https://www.space-track.org/basicspacedata/query/class/gp"

    return (
        f"{base}"
        f"/LAUNCH_DATE/{launch_date}"
        f"/SITE/{launch_site}"
        "/DECAY_DATE/null-val"
        "/EPOCH/%3Enow-10"
        "/format/tle"
    )


def _get_credentials():
    """
    Fetch Space-Track credentials from environment variables.

    To set credentials, set the environment variables SPACETRACK_USERNAME and SPACETRACK_PASSWORD by
    1) open powershell
    2) type $env:SPACETRACK_USERNAME = "username"
    3) type $env:SPACETRACK_PASSWORD = "password"
    """
    username = (os.getenv("SPACETRACK_USERNAME"))
    password = (os.getenv("SPACETRACK_PASSWORD"))

    if not username or not password:
        raise RuntimeError(
            "Space-Track credentials not found. "
            "Set SPACETRACK_USERNAME and SPACETRACK_PASSWORD in your environment."
        )
    return username, password


def _http_get_basic_auth(url, username, password, timeout=30.0):
    """
    Perform a GET request with HTTP Basic authentication using stdlib.
    """
    credentials = f"{username}:{password}".encode("ascii")
    encoded = base64.b64encode(credentials).decode("ascii")

    req = Request(url)
    req.add_header("Authorization", f"Basic {encoded}")

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except HTTPError as e:
        if e.code == 401:
            raise RuntimeError("Space-Track authentication failed (HTTP 401).") from e
        raise RuntimeError(f"Space-Track HTTP error {e.code}: {e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Failed to reach Space-Track: {e.reason}") from e

    try:
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError("Failed to decode Space-Track response as UTF-8.") from e


def fetch_tles(launch_date, launch_site):
    """
    Single bulk Space-Track request filtered by launch_date and launch_site.

    This function is designed so that it cannot violate Space-Track API limits

    - Uses a single GP (aka TLEs) request per call (no per-object queries).
    - Enforces an effective cache TTL of at least 1 hour for GP data, so a
      given environment will never issue GP queries more frequently than
      Space-Track's "1 per hour" guideline.
    - A global rate-state file in the user home directory records the timestamp
      of the last GP query; if another GP query is attempted within 1 hour and
      no valid cache is available, an error is raised instead of calling the
      API again.

    Because the GP request is capped at 1 per hour, this function also cannot
    approach the broader throttling limits (30 requests per minute, 300 per
    hour)

    Parameters
    ----------
    launch_date : str
        Launch date filter from config
    launch_site : str
        Launch site code filter from config

    Returns
    -------
    list
        List of TLE text lines 
    """

    cache_path = _cache_file(
        launch_date,
        launch_site,
        Path(cache_dir) if cache_dir is not None else None,
    )

    # First, try to serve from cache without touching the API at all.
    cached = _load_cached_tles(cache_path, _CACHE_HOURS)
    if cached is not None:
        return cached

    # No valid cache: enforce global 1/hour GP limit using a shared rate state.
    now = datetime.now(timezone.utc)
    last_gp = _load_rate_state()
    if last_gp is not None:
        delta = now - last_gp
        if delta < timedelta(hours=1):
            raise RuntimeError(
                "Space-Track GP query suppressed to respect the 1/hour limit. "
                f"Last GP query was at {last_gp.isoformat()} UTC. "
                "Wait at least 1 hour between GP (TLE) queries or rely on cached data."
            )

    username, password = _get_credentials()
    url = _build_gp_query_url(launch_date, launch_site)

    response_text = _http_get_basic_auth(url, username, password)
    stripped = response_text.strip()

    if not stripped or stripped.upper() == "NO RESULTS RETURNED":
        raise RuntimeError(
            f"Space-Track GP query returned no TLEs for LAUNCH_DATE={launch_date}, "
            f"SITE={launch_site}."
        )

    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("Space-Track GP query response contained no non-empty lines.")

    # Update cache and global rate state after a successful query.
    _save_cached_tles(cache_path, lines)
    _save_rate_state(now)

    return lines