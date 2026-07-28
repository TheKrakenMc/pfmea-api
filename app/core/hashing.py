import logging
import bcrypt

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with exactly 10 rounds.
    Conforms to industrial security guidelines (e.g., TISAX).
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=10)
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using bcrypt in constant time.
    """
    try:
        plain_pwd_bytes = plain_password.encode('utf-8')
        hashed_pwd_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_pwd_bytes, hashed_pwd_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False
