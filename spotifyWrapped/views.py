import os
import requests
import base64
import urllib.parse
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from requests import request

from .forms import UserRegisterForm
from .models import SpotifyWrap, DuoWrapped, UserProfile
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from .utils import refresh_spotify_token
from django.utils.timezone import now
from django.utils import timezone




# Spotify OAuth Constants
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
SPOTIFY_SCOPE = 'user-top-read user-read-recently-played'

def fetch_spotify_data(user_profile):
    try:
        if user_profile.token_expires_at <= timezone.now():
            refreshed = refresh_spotify_token(user_profile)
            if not refreshed:
                messages.error(request, "Failed to refresh Spotify token.")
                return None

        # Set up the authorization header with the access token
        headers = {
            'Authorization': f'Bearer {user_profile.spotify_access_token}',
        }

        # Fetch top artists, tracks, and recently played tracks
        artists_response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)
        tracks_response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
        recent_response = requests.get('https://api.spotify.com/v1/me/player/recently-played', headers=headers)

        # Handle errors in any response
        if artists_response.status_code != 200 or tracks_response.status_code != 200 or recent_response.status_code != 200:
            print("Failed to fetch Spotify data")
            return None

        # Return the collected data as a dictionary
        return {
            'top_artists': artists_response.json(),
            'top_tracks': tracks_response.json(),
            'recent_played': recent_response.json(),
        }
    except Exception as e:
        print(f"Error fetching Spotify data: {str(e)}")
        return None

def index(request):
    return render(request, 'index.html')


def signup_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # After creating the user, redirect to Spotify login
            return redirect('spotify_login')
        else:
            messages.error(request, "Invalid registration details")
    else:
        form = UserRegisterForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # If user has Spotify tokens, redirect to profile
            if hasattr(user, 'UserProfile') and user.UserProfile.spotify_access_token:
                return redirect('profile')
            else:
                # Redirect to Spotify login
                return redirect('spotify_login')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')


def spotify_login(request):
    """
    Direct user to Spotify's authorization page.
    """
    client_id = settings.SPOTIFY_CLIENT_ID
    redirect_uri = 'http://localhost:8000/spotify/callback/'  # Adjust for your environment
    scope = SPOTIFY_SCOPE
    state = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')

    request.session['spotify_auth_state'] = state  # Store state in session for CSRF protection

    auth_url = (
        f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={client_id}"
        f"&scope={urllib.parse.quote(scope)}&redirect_uri={urllib.parse.quote(redirect_uri)}&state={state}"
    )
    return redirect(auth_url)


def spotify_callback(request):
    """
    Handle Spotify's response after user authentication.
    """
    error = request.GET.get('error')
    if error:
        messages.error(request, "Spotify authentication failed.")
        return redirect('login')

    state = request.GET.get('state')
    stored_state = request.session.get('spotify_auth_state')

    # Check for state mismatch for security
    if not stored_state or state != stored_state:
        messages.error(request, "State mismatch. Please try again.")
        return redirect('login')

    code = request.GET.get('code')
    if not code:
        messages.error(request, "Authorization code missing.")
        return redirect('login')

    # Exchange authorization code for access token
    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8000/spotify/callback/'
    }

    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    if response.status_code != 200:
        messages.error(request, "Failed to obtain access token from Spotify.")
        return redirect('login')

    token_info = response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')  # in seconds
    expires_at = timezone.now() + timedelta(seconds=expires_in)

    # Store the access token in the user's profile
    user_profile = request.user.userprofile
    user_profile.spotify_access_token = access_token
    user_profile.spotify_refresh_token = refresh_token
    user_profile.token_expires_at = expires_at
    user_profile.save()

    # Fetch the user's Spotify profile using the access token
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    user_response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers)
    if user_response.status_code != 200:
        messages.error(request, "Failed to fetch Spotify user profile.")
        return redirect('login')

    spotify_user_id = user_response.json().get('id')
    user_profile.spotify_user_id = spotify_user_id
    user_profile.save()

    messages.success(request, "Spotify account successfully connected!")
    return redirect('profile')

    # Ensure user is authenticated on the website
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.spotify_user_id = spotify_user_id
        user_profile.spotify_access_token = access_token
        user_profile.spotify_refresh_token = refresh_token
        user_profile.token_expires_at = expires_at
        user_profile.save()

        messages.success(request, "Spotify account successfully connected!")
        return redirect('profile')
    else:
        messages.error(request, "User authentication failed.")
        return redirect('login')

@login_required
def wrapped_detail(request, wrap_id):
    wrap = SpotifyWrap.objects.get(id=wrap_id, user_profile=request.user.userprofile)
    return render(request, 'wrapped_detail.html', {'wrap': wrap})

def duo_wrapped(request, duo_id):
    duo = DuoWrapped.objects.get(id=duo_id)
    return render(request, 'duo_wrapped.html', {'duo': duo})

def contact_view(request):
    if request.method == 'POST':
        # Handle form submission (e.g., send email)
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'

        # Implement email sending logic here using Django's EmailMessage or similar
        # Example:
        # from django.core.mail import send_mail
        # send_mail(subject, message, user_email, ['support@spotifywrapper.com'])

        messages.success(request, "Your message has been sent. We'll get back to you shortly.")
        return redirect('contact')
    return render(request, 'contact.html')

@login_required
def wrapped_presentation(request):
    user_profile = request.user.userprofile
    spotify_data = fetch_spotify_data(user_profile)

    if spotify_data:
        SpotifyWrap.objects.create(
            user_profile=user_profile,
            total_minutes_watched=spotify_data['recent_played'].get('total', 0),
            top_artists=", ".join([artist['name'] for artist in spotify_data['top_artists']['items']]),
            most_played_song=spotify_data['top_tracks']['items'][0]['name'] if spotify_data['top_tracks']['items'] else '',
            year=datetime.now().year
        )
    else:
        messages.error(request, "Failed to fetch Spotify data.")
        return redirect('profile')

    return render(request, 'wrapped_presentation.html', {'spotify_data': spotify_data})

@login_required
def profile_view(request):
    user_profile = request.user.userprofile
    wraps = SpotifyWrap.objects.filter(user_profile=user_profile)

    spotify_data = fetch_spotify_data(user_profile)
    return render(request, 'profile.html', {'wraps': wraps, 'spotify_data': spotify_data})

@login_required
def delete_account(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        user = request.user
        SpotifyWrap.objects.filter(user_profile=user_profile).delete()
        DuoWrapped.objects.filter(user_profile=user_profile).delete()
        user_profile.delete()
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('index')
    return render(request, 'delete_account.html')

@login_required
def delete_wrap(request, wrap_id):
    try:
        wrap = SpotifyWrap.objects.get(id=wrap_id, user_profile=request.user.userprofile)
        wrap.delete()
        messages.success(request, "Wrap deleted successfully.")
    except SpotifyWrap.DoesNotExist:
        messages.error(request, "Wrap not found.")

    return redirect('profile')


@login_required
def past_wraps_view(request):
    # Fetch the past wraps for the logged-in user
    user = request.user  # This fetches the logged-in user
    wraps = SpotifyWrap.objects.filter(user=user)  # Fetch past wrap data for the user

    # Context for the template
    context = {
        'wraps': wraps
    }
    return render(request, 'wraps.html', context)