"""Utilities for parsing, validating, and comparing ISO-8601 timestamps."""

from datetime import datetime, timezone
from typing import Optional, Union

def parse_iso_timestamp(ts: Union[str, datetime]) -> datetime:
    """Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime.
    
    If already a datetime, ensure it is timezone-aware in UTC.
    """
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    
    clean_ts = str(ts).strip()
    # Normalize trailing Z to +00:00 for fromisoformat compatibility
    if clean_ts.endswith('Z'):
        clean_ts = clean_ts[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception as e:
        raise ValueError(f"Invalid timestamp format: {ts} ({e})")

def is_at_or_before(ts1: Union[str, datetime], ts2: Union[str, datetime]) -> bool:
    """Return True if ts1 <= ts2."""
    dt1 = parse_iso_timestamp(ts1)
    dt2 = parse_iso_timestamp(ts2)
    return dt1 <= dt2

def is_strictly_before(ts1: Union[str, datetime], ts2: Union[str, datetime]) -> bool:
    """Return True if ts1 < ts2."""
    dt1 = parse_iso_timestamp(ts1)
    dt2 = parse_iso_timestamp(ts2)
    return dt1 < dt2
