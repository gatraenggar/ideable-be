from decouple import config
import datetime, jwt

class TokenManager():
    def generate_random_token(payload):
        payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=600)
        return jwt.encode(payload, config("RANDOM_TOKEN_KEY"), algorithm="HS256")

    def verify_random_token(token):
        return jwt.decode(token, config("RANDOM_TOKEN_KEY"), algorithms=["HS256"])

    def generate_access_token(uuid):
        payload = {
            "user_uuid": uuid.hex,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=600),
        }
        return jwt.encode(payload, config("ACCESS_TOKEN_KEY"), algorithm="HS256")

    def verify_access_token(token):
        return jwt.decode(token, config("ACCESS_TOKEN_KEY"), algorithms=["HS256"])

    def generate_refresh_token(uuid):
        payload = {
            "user_uuid": uuid.hex,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
        }
        return jwt.encode(payload, config("REFRESH_TOKEN_KEY"), algorithm="HS256")

    def verify_refresh_token(token):
        return jwt.decode(token, config("REFRESH_TOKEN_KEY"), algorithms=["HS256"])
