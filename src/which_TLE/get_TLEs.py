"""Space-Track GP TLE fetch with caching and rate limiting."""

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import requests
from org.orekit.propagation.analytical.tle import TLE

from src.paths import repo_root

_CACHE_HOURS = 2.0

_RATE_STATE_FILE = repo_root() / ".spacetrack_rate_state.json"

_MAX_REQUESTS_PER_MINUTE = 30
_MAX_REQUESTS_PER_HOUR = 300


def _load_rate_state():
    """
    Load the API request log from the rate state file.

    Returns
    -------
    list[datetime]
        UTC datetimes of previous API requests (pruning is done by caller).
    """

    if not _RATE_STATE_FILE.exists():
        return []

    try:
        raw = json.loads(_RATE_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        # If the file is corrupted, fail open but effectively start fresh.
        return []

    timestamps: list[datetime] = []

    # Preferred format: {"request_log_utc": ["iso1", "iso2", ...]}
    if isinstance(raw, dict):
        log = raw.get("request_log_utc")
        if isinstance(log, list):
            for ts in log:
                if not isinstance(ts, str):
                    continue
                try:
                    timestamps.append(datetime.fromisoformat(ts))
                except Exception:
                    continue

        # Backwards compatibility with legacy single-timestamp format:
        # {"last_gp_query_utc": "..."}
        if not timestamps:
            ts = raw.get("last_gp_query_utc")
            if isinstance(ts, str):
                try:
                    timestamps.append(datetime.fromisoformat(ts))
                except Exception:
                    pass

    # Also accept a bare list of ISO strings if present.
    elif isinstance(raw, list):
        for ts in raw:
            if not isinstance(ts, str):
                continue
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except Exception:
                continue

    return timestamps


def _save_rate_state(request_log):
    """
    Write API request log to the rate state file.

    Parameters
    ----------
    request_log : list[datetime]
        UTC datetimes to persist.
    """
    payload = {
        "request_log_utc": [dt.isoformat() for dt in request_log if isinstance(dt, datetime)]
    }

    try:
        _RATE_STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to save rate state to {_RATE_STATE_FILE}: {e}") from e


def _prune_old_requests(request_log, now):
    """
    Drop entries older than 1 hour; caller enforces limits inside this window.

    Parameters
    ----------
    request_log : list[datetime]
    now : datetime
        Current UTC time.

    Returns
    -------
    list[datetime]
    """
    cutoff = now - timedelta(hours=1)
    return [ts for ts in request_log if ts >= cutoff]


def _cache_file(launch_date, launch_site, cache_dir):
    """
    Return the path for the global GP cache file.

    Parameters
    ----------
    launch_date, launch_site : str
        Included for backward compatibility with the previous per-cohort cache
        scheme but ignored. Filtering by launch_date and launch_site is now
        done locally on the cached global dataset.
    cache_dir : str or Path or None
        Optional override for cache directory.
    """
    root = Path(cache_dir) if cache_dir is not None else (Path.home() / ".spacetrack-cache")
    root.mkdir(parents=True, exist_ok=True)
    return root / "tles_gp_full.json"


def _load_cached_gp(cache_path, cache_hours):
    """
    Load cached global GP dataset (JSON) if it is still fresh enough.

    Returns
    -------
    list[dict] or None
        Parsed JSON list of GP records, or None if cache is missing/expired.
    """
    if not cache_path.exists():
        return None
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age_hours = (now - mtime).total_seconds() / 3600.0
    if age_hours > cache_hours:
        return None
    text = cache_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse cached GP JSON from {cache_path}: {e}") from e
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected GP cache format in {cache_path}: expected list, got {type(data).__name__}")
    return data


def _save_cached_gp(cache_path, records):
    """
    Save global GP dataset (JSON) to cache.

    Parameters
    ----------
    records : list[dict]
        GP objects as returned by Space-Track JSON endpoint.
    """
    try:
        cache_path.write_text(json.dumps(records), encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to save cached GP JSON to {cache_path}: {e}") from e


def _build_gp_query_url():
    """
    Build Space-Track GP query URL for a global on-orbit, recent-EPOCH dataset.

    Notes
    -----
    We keep:
    - DECAY_DATE/null-val  (on-orbit only)
    - EPOCH/>now-10        (only TLEs from the last 10 days)

    The caller filters this global dataset locally by LAUNCH_DATE and SITE.
    """
    # Use JSON so LAUNCH_DATE and SITE are available for local filtering, and
    # request empty results to be shown (otherwise Space-Track may return a blank
    # page/body for empty queries).
    base = (
        "https://www.space-track.org/basicspacedata/query/class/gp/orderby/CCSDS_OMM_VERS%20asc/emptyresult/show"
    )

    return (
        base
    )


def _acquire_gp_dataset(cache_dir, *, quiet: bool = False):
    """
    Return the full GP record list: from cache if fresh, else one bulk API fetch.

    This is the same path ``fetch_tles`` uses before cohort filtering: local
    ``tles_gp_full.json`` under ``cache_dir`` must exist and be newer than
    ``_CACHE_HOURS``; otherwise credentials are required and rate limits apply.

    Parameters
    ----------
    cache_dir : str or Path or None
        Directory for ``tles_gp_full.json`` (same as ``fetch_tles``).
    quiet : bool
        If True, do not print cache/API messages (for internal reuse).

    Returns
    -------
    list[dict]
        GP records as returned by Space-Track JSON.
    """
    cache_path = _cache_file("", "", cache_dir)

    cached_records = _load_cached_gp(cache_path, _CACHE_HOURS)

    if cached_records is not None:
        if not quiet:
            print(f"[Space-Track] Using cached GP dataset from {cache_path}")
        return cached_records

    now = datetime.now(timezone.utc)
    request_log = _load_rate_state()
    request_log = _prune_old_requests(request_log, now)

    one_minute_ago = now - timedelta(minutes=1)
    recent_minute = [ts for ts in request_log if ts >= one_minute_ago]
    if len(recent_minute) >= _MAX_REQUESTS_PER_MINUTE:
        raise RuntimeError(
            "Space-Track request suppressed to respect the 30-per-minute limit. "
            f"{len(recent_minute)} requests have been logged in the last 60 seconds. "
            "Wait before issuing additional Space-Track queries."
        )

    if len(request_log) >= _MAX_REQUESTS_PER_HOUR:
        raise RuntimeError(
            "Space-Track request suppressed to respect the 300-per-hour limit. "
            f"{len(request_log)} requests have been logged in the last hour. "
            "Wait before issuing additional Space-Track queries."
        )

    if request_log:
        last_gp = max(request_log)
        if now - last_gp < timedelta(hours=1):
            raise RuntimeError(
                "Space-Track GP query suppressed to respect the 1/hour limit. "
                f"Last GP query was at {last_gp.isoformat()} UTC. "
                "Wait at least 1 hour between GP (TLE) queries or rely on cached data."
            )

    request_log.append(now)
    _save_rate_state(request_log)

    username, password = _get_credentials()
    url = _build_gp_query_url()

    if not quiet:
        print(f"[Space-Track] Fetching fresh GP dataset from API: {url}")
    response_text = _http_get_spacetrack(url, username, password)
    stripped = response_text.strip()

    if not stripped:
        raise RuntimeError(
            f"URL: {url} Space-Track GP query returned an empty response."
        )

    try:
        records = json.loads(stripped)
    except Exception as e:
        raise RuntimeError("Failed to parse Space-Track GP JSON response.") from e

    if not isinstance(records, list) or not records:
        raise RuntimeError(
            f"URL: {url} Space-Track GP query returned no records."
        )

    _save_cached_gp(cache_path, records)
    return records


def _gp_records_for_norad(records, norad_id: int):
    """Filter GP JSON records to those matching NORAD_CAT_ID with TLE lines."""
    target = str(int(norad_id))
    out = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        if str(rec.get("NORAD_CAT_ID", "")).strip() != target:
            continue
        l1 = rec.get("TLE_LINE1")
        l2 = rec.get("TLE_LINE2")
        if isinstance(l1, str) and isinstance(l2, str) and l1.startswith("1 ") and l2.startswith("2 "):
            out.append(rec)
    return out


def _pick_latest_gp_record(matches: list) -> dict:
    """If multiple GP rows exist for one NORAD, prefer the latest EPOCH string."""
    if len(matches) == 1:
        return matches[0]

    def epoch_key(rec):
        ep = rec.get("EPOCH")
        return ep if isinstance(ep, str) else ""

    return max(matches, key=epoch_key)


def get_tle_for_norad_id(norad_id, cache_dir=None):
    """
    Return a single Orekit ``TLE`` for ``NORAD_CAT_ID``.

    Uses the same bulk GP cache and API policy as :func:`fetch_tles`:

    - If ``<cache_dir>/tles_gp_full.json`` exists and is younger than
      ``_CACHE_HOURS``, records are read from disk (no HTTP).
    - Otherwise one bulk GP request may be issued (rate limits + credentials),
      same as :func:`fetch_tles`.
    - Records are filtered by ``NORAD_CAT_ID``; if none match, raises (the bulk
      snapshot may omit an object; refresh the cache or verify the ID).

    Parameters
    ----------
    norad_id : int
        Space-Track NORAD catalog ID.
    cache_dir : str or Path or None
        Same as ``fetch_tles`` (defaults to home ``.spacetrack-cache`` if None).

    Returns
    -------
    org.orekit.propagation.analytical.tle.TLE
    """
    records = _acquire_gp_dataset(cache_dir)
    matches = _gp_records_for_norad(records, norad_id)

    if not matches:
        raise RuntimeError(
            f"No GP record with TLE lines found for NORAD_CAT_ID={int(norad_id)}."
        )

    rec = _pick_latest_gp_record(matches)
    l1 = rec["TLE_LINE1"].strip()
    l2 = rec["TLE_LINE2"].strip()
    return TLE(l1, l2)


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



def _http_get_spacetrack(url, username, password, timeout=30.0):
    with requests.Session() as s:
        login = s.post(
            "https://www.space-track.org/ajaxauth/login",
            data={"identity": username, "password": password},
            timeout=timeout,
        )
        login.raise_for_status()

        r = s.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text

def fetch_tles(launch_date, launch_site, cache_dir=None):
    """
    Single bulk Space-Track request filtered by launch_date and launch_site.

    This function is designed so that it cannot violate Space-Track API limits.

    - Uses a single GP (aka TLEs) request per call (no per-object queries).
    - Enforces an effective cache TTL of at least 1 hour for GP data, so a
      given environment will never issue GP queries more frequently than
      Space-Track's "1 per hour" guideline.
    - A global JSON rate-state file in the user home directory records timestamps
      for every API attempt. Before any HTTP call is made, this log is consulted
      to guarantee that no more than 30 requests are made in any rolling
      60-second window and no more than 300 requests are made in any rolling
      1-hour window, even if the API returns errors or "NO RESULTS RETURNED".
    - If any of these limits would be exceeded, the API call is skipped and a
      RuntimeError is raised instead.

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

    # Shared with get_tle_for_norad_id: cache-first bulk GP, then one API fetch if stale.
    records = _acquire_gp_dataset(cache_dir)

    # Helper: given a list of GP records, filter locally by launch cohort and
    # return TLE line pairs as a flat list of strings.
    def _filter_records(gp_records):
        cohort = [
            rec
            for rec in gp_records
            if rec.get("LAUNCH_DATE") == launch_date and rec.get("SITE") == launch_site
        ]
        if not cohort:
            raise RuntimeError(
                "Space-Track GP cache contains no TLEs for "
                f"LAUNCH_DATE={launch_date}, SITE={launch_site}."
            )
        lines = []
        for rec in cohort:
            l1 = rec.get("TLE_LINE1")
            l2 = rec.get("TLE_LINE2")
            if l1 and l2:
                lines.append(l1)
                lines.append(l2)
        if not lines:
            raise RuntimeError(
                "Space-Track GP cache records for the requested cohort are missing TLE lines."
            )
        return lines

    return _filter_records(records)


def get_candidate_tles(cfg):
    """Space-Track GP cohort -> list of Orekit TLE (caller must have run setup_orekit)."""
    lines = fetch_tles(cfg.launch_date, cfg.launch_site, cache_dir=getattr(cfg, "cache_dir", None))
    tles = []
    i = 0
    while i < len(lines):
        line1 = lines[i].strip()
        if line1.startswith("1 ") and i + 1 < len(lines):
            line2 = lines[i + 1].strip()
            if line2.startswith("2 "):
                tles.append(TLE(line1, line2))
                i += 2
                continue
        i += 1
    return tles


def get_candidate_tles_from_file(filepath):
    """
    Load Orekit TLE objects from a local file (no Space-Track API).

    File format: TLE line pairs (line 1 starting with "1 ", line 2 with "2 "),
    one pair per object. Blank lines are skipped.

    Parameters
    ----------
    filepath : str or Path
        Path to .tle or text file.

    Returns
    -------
    list
        List of Orekit TLE objects.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"TLE file not found: {path}")
    text = path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tles = []
    i = 0
    while i < len(lines):
        line1 = lines[i]
        if line1.startswith("1 ") and i + 1 < len(lines):
            line2 = lines[i + 1]
            if line2.startswith("2 "):
                tles.append(TLE(line1, line2))
                i += 2
                continue
        i += 1
    return tles