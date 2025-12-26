"""
Resilience Utilities.
Decorator untuk Retry otomatis menggunakan Tenacity.
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Retry standar untuk operasi Database/Network
# - Coba maksimal 3 kali
# - Tunggu eksponensial (1s, 2s, 4s...)
# - Log warning sebelum retry
def retry_standard(max_attempts: int = 3):
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, "WARNING"), # type: ignore
        reraise=True
    )

# Contoh penggunaan:
# @retry_standard()
# async def call_external_api(): ...