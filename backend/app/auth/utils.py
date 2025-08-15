import random
import string
import bcrypt
import secrets

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
