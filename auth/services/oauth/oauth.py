from decouple import config
import json, requests

class OAuth():
    def request_user_consent():
        clientID = config("GOOGLE_OAUTH_CLIENT_ID")
        redirectURI = config("HOST") + "/v1/oauth/google/login/callback"
        emailScope = "https://www.googleapis.com/auth/userinfo.email"
        profileScope = "https://www.googleapis.com/auth/userinfo.profile"

        authURI = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={}&redirect_uri={}&scope={}+{}"
        ).format(clientID, redirectURI, emailScope, profileScope)
        return authURI

    def request_user_info(auth_code):
        oauthConfig = {
            "code": auth_code,
            "client_id": config("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": config("GOOGLE_OAUTH_CLIENT_SECRET"),
            "redirect_uri": config("HOST") + "/v1/oauth/google/login/callback",
            "grant_type": "authorization_code"
        }
        oauthToken = requests.post('https://oauth2.googleapis.com/token', data=oauthConfig)
        
        userInfoResponse = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={
            'Authorization': "Bearer " + json.loads(oauthToken.text)["access_token"]
        })
        return json.loads(userInfoResponse.text)
