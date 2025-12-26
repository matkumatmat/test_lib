"""
Security Obfuscation Module.
1. IDObfuscator: Mengubah Integer ID -> String Acak (via Sqids).
2. Obfuscator: Masking data sensitif (Email, Phone, CC) untuk logging.
"""
import re
from typing import Any, Dict

try:
    from sqids import Sqids
except ImportError: # pragma: no cover
    Sqids = None # type: ignore

class IDObfuscator:
    def __init__(self, secret_salt: str = "", min_length: int = 8):
        if Sqids is None:
            raise ImportError(
                "Library 'sqids' diperlukan. Install: 'poetry add sqids'"
            )
        
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        if secret_salt:
            alphabet = self._shuffle_alphabet(alphabet, secret_salt)

        self.sqids = Sqids(min_length=min_length, alphabet=alphabet)

    def encode(self, id: int) -> str:
        return self.sqids.encode([id])

    def decode(self, hash_id: str) -> int | None:
        decoded = self.sqids.decode(hash_id)
        return decoded[0] if decoded else None

    def _shuffle_alphabet(self, alphabet: str, salt: str) -> str:
        chars = list(alphabet)
        salt_chars = list(salt)
        salt_len = len(salt)
        for i in range(len(chars) - 1, 0, -1):
            p = ord(salt_chars[i % salt_len])
            j = (i * p) % (i + 1)
            chars[i], chars[j] = chars[j], chars[i]
        return "".join(chars)


class Obfuscator:
    """
    Utility untuk menyensor data sensitif (PII) sebelum masuk log/response.
    """
    
    @staticmethod
    def mask_email(email: str) -> str:
        """johndoe@example.com -> j*****e@example.com"""
        if not email or "@" not in email:
            return email
            
        try:
            user, domain = email.split("@")
            if len(user) > 2:
                # Ambil huruf pertama dan terakhir, tengah dibintang
                masked_user = f"{user[0]}{'*' * 5}{user[-1]}"
            else:
                # Kalau user pendek (a@b.com), bintangin sebagian
                masked_user = f"{user[0]}*"
            
            return f"{masked_user}@{domain}"
        except Exception:
            return email

    @staticmethod
    def mask_phone(phone: str) -> str:
        """081234567890 -> ********7890"""
        if not phone or len(phone) < 4:
            return "***"
        return "*" * (len(phone) - 4) + phone[-4:]

    @staticmethod
    def mask_credit_card(cc: str) -> str:
        """1234567812345678 -> ************5678"""
        # Hapus spasi/dash dulu
        clean_cc = re.sub(r"\D", "", cc)
        if len(clean_cc) < 4:
            return "***"
        return "*" * (len(clean_cc) - 4) + clean_cc[-4:]

    @staticmethod
    def mask_string(text: str, visible_start: int = 0, visible_end: int = 0) -> str:
        """Masking generik: abcdefg -> ab***fg"""
        if not text:
            return ""
        
        length = len(text)
        if visible_start + visible_end >= length:
            return text
            
        return (
            text[:visible_start] + 
            "*" * 12 +  # Fixed length asterisk biar gak ngebocorin panjang asli
            text[length - visible_end:]
        )

    @classmethod
    def obfuscate_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Membersihkan dictionary dari field sensitif (password, token, dll).
        Cocok untuk sanitasi log.
        """
        SENSITIVE_KEYS = {"password", "token", "secret", "access_token", "refresh_token", "credit_card"}
        PII_KEYS = {"email", "phone", "mobile", "ktp", "nik"}
        
        clean_data = data.copy()
        
        for key, value in clean_data.items():
            k = key.lower()
            if isinstance(value, dict):
                clean_data[key] = cls.obfuscate_dict(value)
            elif isinstance(value, str):
                if k in SENSITIVE_KEYS:
                    clean_data[key] = "********"
                elif k in PII_KEYS:
                    if "email" in k:
                        clean_data[key] = cls.mask_email(value)
                    elif "phone" in k or "mobile" in k:
                        clean_data[key] = cls.mask_phone(value)
                    else:
                        clean_data[key] = cls.mask_string(value, 2, 2)
                        
        return clean_data