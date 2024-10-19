import requests
import base64
from datetime import datetime, timedelta
from django.conf import settings
from .models import UserProfile

SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

def refresh_spotify_token(user_profile):
    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': user_profile.spotify_refresh_token
    }

    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    if response.status_code != 200:
        return False

    token_info = response.json()
    access_token = token_info.get('access_token')
    expires_in = token_info.get('expires_in')  # in seconds
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    user_profile.spotify_access_token = access_token
    user_profile.token_expires_at = expires_at
    user_profile.save()
    return True
