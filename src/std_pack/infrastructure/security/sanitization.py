"""
Security Sanitization Module.
Versi Aggressive: Validasi input string dengan deteksi Tautology (1=1).
"""
import re
from typing import ClassVar, List

class InputSanitizer:
    # Menggunakan List Regex agar lebih mudah dibaca dan dimaintain
    UNSAFE_PATTERNS: ClassVar[List[str]] = [
        # 1. SQL Injection Keywords (Case Insensitive)
        r"(?i)\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC)\b",
        
        # 2. SQL Comments
        r"--", 
        r"/\*",
        
        # 3. SQL Tautologies (Logic 1=1, a=a, x=x)
        # Penjelasan: \b(\w+) menangkap kata/angka, \s*=\s* menangkap =, \1 mengecek apakah sama dengan kata pertama
        r"(?i)\b(\w+)\s*=\s*\1\b", 
        
        # 4. OR based injection (' OR '1'='1)
        r"(?i)['\"]\s*OR\s*['\"]?\w+['\"]?\s*=\s*['\"]?\w+",
        
        # 5. XSS Patterns
        r"(?i)(<script|<iframe|javascript:|onerror=|onload=|alert\()",
    ]

    @classmethod
    def is_safe(cls, value: str) -> bool:
        """Return True jika bersih, False jika terdeteksi pola berbahaya."""
        if not value:
            return True
            
        # Loop semua pattern, jika ada satu saja yang cocok -> UNSAFE
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, value):
                return False
                
        return True

    @classmethod
    def clean(cls, value: str) -> str:
        """Membersihkan karakter kontrol (Null bytes, dll)."""
        # Hapus null bytes dan karakter kontrol non-printable
        return "".join(ch for ch in value if ord(ch) >= 32 or ch in "\n\t")