import hashlib
import secrets

from models import User

def generate_salt():
    """
    Generate a random salt using the secrets module.
    """
    return secrets.token_hex(16)

def hash_password(password:str, salt:str):
    """
    Hash the given password using the provided salt.
    """
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed_password.hex()


def check_password(password:str,user:User):
    salt = user.salt
    hashed_password = hash_password(password,salt)
    # Compare the hashed passwords
    if hashed_password == user.hashedPassword:
        return True
    else:
        return False


