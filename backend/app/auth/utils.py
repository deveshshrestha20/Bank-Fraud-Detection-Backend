import random
import string
import uuid
from datetime import datetime, timedelta
from time import timezone

import bcrypt
import secrets

import jwt

from backend.app.core.config import settings


# Generate OTP

def generate_otp(length:int=6) -> str:
    return "".join(random.choices(string.digits, k=length))



# Hash a password

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')



def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_username(first_name: str, last_name: str, length=4) -> str:
    random_digits = ''.join(secrets.choice(string.digits) for _ in range(length))
    username = f"{first_name.lower()}.{last_name.lower()}{random_digits}"
    return username

def create_activation_token(id: uuid.UUID) -> str:
    payload = {
        "id": str(id),
        "type": "activation",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACTIVATION_TOKEN_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
