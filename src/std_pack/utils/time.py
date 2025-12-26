"""
Time Utilities.
Memastikan semua operasi waktu menggunakan Timezone Aware (UTC).
"""
from datetime import datetime, timedelta, timezone, date

def now_utc() -> datetime:
    """Return datetime sekarang dalam UTC."""
    return datetime.now(timezone.utc)

def to_iso_string(dt: datetime) -> str:
    """Convert datetime ke format string ISO 8601."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def from_unix_timestamp(ts: float | int) -> datetime:
    """Convert Unix Timestamp ke UTC Datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)

# --- FUNGSI DARI V1 (ADAPTED) ---

def start_of_day(dt: datetime | None = None) -> datetime:
    """Awal hari (00:00:00) dalam UTC."""
    if dt is None:
        dt = now_utc()
    return datetime.combine(dt.date(), datetime.min.time(), tzinfo=timezone.utc)

def end_of_day(dt: datetime | None = None) -> datetime:
    """Akhir hari (23:59:59.999) dalam UTC."""
    if dt is None:
        dt = now_utc()
    return datetime.combine(dt.date(), datetime.max.time(), tzinfo=timezone.utc)

def add_days(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)

def diff_in_minutes(dt1: datetime, dt2: datetime) -> float:
    """Selisih menit (absolut)."""
    return abs((dt2 - dt1).total_seconds() / 60)    