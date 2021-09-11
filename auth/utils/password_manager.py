from argon2 import exceptions, PasswordHasher
ph = PasswordHasher()

class PasswordManager():
    def hash(password):
        return ph.hash(password)

    def verify(hashed, password):
        try:
            isVerified = ph.verify(hashed, password)
            return isVerified
        except Exception as e:
            if isinstance(e, exceptions.VerifyMismatchError):
                return False
            else: raise e
