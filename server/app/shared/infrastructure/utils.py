import hashlib


def hash_raw_str(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
