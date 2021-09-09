from decouple import config
import jwt

class TokenManager():
    def encode(payload):
        return jwt.encode(payload, config("ACCESS_TOKEN_KEY"), algorithm="HS256")

    def decode(token):
        return jwt.decode(token, config("ACCESS_TOKEN_KEY"), algorithms=["HS256"])
