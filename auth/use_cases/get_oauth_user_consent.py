from auth.services.oauth.oauth import OAuth

def get_oauth_user_consent():
    return OAuth.request_user_consent()
