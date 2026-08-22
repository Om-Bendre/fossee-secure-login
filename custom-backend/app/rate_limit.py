import time

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
_failed_attempts: dict[str, dict] = {}

def is_locked(email: str) -> bool:
    entry = _failed_attempts.get(email)
    return bool(entry and entry["locked_until"] > time.time())

def record_failure(email: str):
    entry = _failed_attempts.setdefault(email, {"count": 0, "locked_until": 0})
    entry["count"] += 1
    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["locked_until"] = time.time() + LOCKOUT_SECONDS
        entry["count"] = 0

def clear_failures(email: str):
    _failed_attempts.pop(email, None)

def clear_all_failures():
    _failed_attempts.clear()
