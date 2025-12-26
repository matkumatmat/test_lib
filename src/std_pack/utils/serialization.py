"""
Serialization Utilities.
Menggunakan 'orjson' untuk parsing JSON super cepat.
"""
from typing import Any

import orjson

def to_json(data: Any) -> str:
    """
    Dump object ke JSON string (bytes -> decode utf-8).
    Menangani numpy, datetime, dan dataclasses secara otomatis via orjson.
    """
    # OPT_NON_STR_KEYS: Izinkan dict key selain string
    # OPT_SERIALIZE_NUMPY: Support numpy array
    return orjson.dumps(
        data, 
        option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
    ).decode("utf-8")

def from_json(json_str: str | bytes) -> Any:
    """Parse JSON string/bytes ke Python Object."""
    return orjson.loads(json_str)

def to_json_bytes(data: Any) -> bytes:
    """Dump langsung ke bytes (lebih efisien untuk kirim ke Network/Redis)."""
    return orjson.dumps(data)