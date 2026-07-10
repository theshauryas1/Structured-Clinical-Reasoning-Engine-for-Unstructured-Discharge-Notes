import hashlib
import secrets
import datetime
from sqlalchemy.orm import Session
from backend.db.models import UserSession

def hash_password(password: str) -> str:
    # Generate a random 16-byte salt
    salt = secrets.token_hex(16)
    # Perform 100,000 iterations of PBKDF2-HMAC-SHA256
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    h = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return f"pbkdf2_sha256:100000:{salt}:{h.hex()}"

def verify_password(password: str, pw_hash: str) -> bool:
    try:
        parts = pw_hash.split(':')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = parts[2]
        stored_hash = parts[3]
        
        pwd_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        h = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
        return h.hex() == stored_hash
    except Exception:
        return False

def create_session(db: Session, user_id: str) -> str:
    token = secrets.token_hex(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    user_session = UserSession(token=token, user_id=user_id, expires_at=expires_at)
    db.add(user_session)
    db.commit()
    return token

def verify_session(db: Session, token: str) -> str | None:
    if not token:
        return None
    session_record = db.query(UserSession).filter(UserSession.token == token).first()
    if not session_record:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = session_record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=datetime.timezone.utc)
    if expires < now:
        try:
            db.delete(session_record)
            db.commit()
        except Exception:
            pass
        return None
    return session_record.user_id
