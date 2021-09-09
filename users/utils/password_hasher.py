from main.errors.client_error import ClientError
from argon2 import PasswordHasher
ph = PasswordHasher()

class Hasher():
    def hash_password(password):
        return ph.hash(password)

    def verify_password(hash, password):
        try:
            isVerified = ph.verify(hash, password)
            if not isVerified:
                raise ClientError("Invalid Password")
            return isVerified
        except ClientError as e:
            return e
