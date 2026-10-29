"""Security, hashing, and audit serialization utilities."""
import hashlib
import json
import secrets
from typing import Any

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 600,000 iterations and 16-byte salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600_000
    )
    return f"pbkdf2:sha256:600000${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against pbkdf2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        algorithm_meta, salt, expected_key = parts
        _, _, iterations = algorithm_meta.split(":")
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations)
        )
        return secrets.compare_digest(computed_key.hex(), expected_key)
    except Exception:
        return False

def generate_session_token() -> str:
    """Generate cryptographically secure 32-byte hex token."""
    return secrets.token_hex(32)

def canonical_json(obj: Any) -> str:
    """Serialize object deterministically with sorted keys and compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def calculate_event_hash(prev_hash: str, canonical_payload: str) -> str:
    """Compute SHA-256 hash chaining previous event hash and canonical payload."""
    combined = f"{prev_hash}|{canonical_payload}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def sanitize_csv_cell(value: Any) -> str:
    """Escape potential spreadsheet formula injection characters (=, +, -, @, TAB, CR)."""
    if value is None:
        return ""
    val_str = str(value)
    if val_str and val_str[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val_str}"
    return val_str
