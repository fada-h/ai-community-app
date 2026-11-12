"""认证：密码哈希（scrypt）+ 无状态 Token（HMAC-SHA256）。"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from .config import settings


def hash_password(password: str) -> str:
    """scrypt 加盐哈希，格式 scrypt$salt$hash。"""
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt.encode("utf-8"), n=16384, r=8, p=1, dklen=32
    )
    return "scrypt$" + salt + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """定长比较，避免时序攻击。"""
    try:
        scheme, salt, expected = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt.encode("utf-8"), n=16384, r=8, p=1, dklen=32
    )
    return hmac.compare_digest(digest.hex(), expected)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def create_token(user_id: int) -> str:
    """签发 Token：payload.signature。"""
    payload = {
        "uid": user_id,
        "exp": int(time.time()) + settings.access_token_expire_minutes * 60,
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _b64(
        hmac.new(settings.secret_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    return body + "." + signature


def parse_token(token: str) -> dict | None:
    """校验 Token，返回 payload 或 None。"""
    if not token or token.count(".") != 1:
        return None
    body, signature = token.split(".")
    expected = _b64(
        hmac.new(settings.secret_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_unb64(body))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload
