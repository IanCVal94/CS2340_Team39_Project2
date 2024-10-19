"""
Views for handling user authentication, Spotify integration, and app functionality.
"""
import os
import base64
import urllib.parse
from datetime import datetime, timedelta

import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail

from .forms import UserRegisterForm
from .models import SpotifyWrap, DuoWrapped, UserProfile
from .utils import refresh_spotify_token


# Spotify OAuth Constants
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
SPOTIFY_SCOPE = 'user-top-read user-read-recently-played'


def fetch_spotify_data(user_profile):
    """
    Fetches Spotify data (top artists, top tracks, and recently played tracks) for the user.

    Args:
        user_profile (UserProfile): The user profile containing the Spotify access token.

    Returns:
        dict: Spotify data containing top artists, top tracks, and recently played tracks.
        None: If data fetch fails.
    """
    try:
        if user_profile.token_expires_at <= timezone.now():
            refreshed = refresh_spotify_token(user_profile)
            if not refreshed:
                return None

        headers = {'Authorization': f'Bearer {user_profile.spotify_access_token}'}
        artists_response = requests.get(
            'https://api.spotify.com/v1/me/top/artists', headers=headers, timeout=10
        )
        tracks_response = requests.get(
            'https://api.spotify.com/v1/me/top/tracks', headers=headers, timeout=10
        )
        recent_response = requests.get(
            'https://api.spotify.com/v1/me/player/recently-played', headers=headers, timeout=10
        )

        if (artists_response.status_code != 200 or tracks_response.status_code != 200
                or recent_response.status_code != 200):
            print("Failed to fetch Spotify data")
            return None

        return {
            'top_artists': artists_response.json(),
            'top_tracks': tracks_response.json(),
            'recent_played': recent_response.json(),
        }
    except (requests.Timeout, requests.RequestException) as e:
        print(f"Error fetching Spotify data: {str(e)}")
        return None


def index(request):
    """
    Renders the index page.
    """
    return render(request, 'index.html')


def signup_view(request):
    """
    Handles user signup and registration.

    Args:
        request (HttpRequest): The request object containing the form data.
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('spotify_login')
        messages.error(request, "Invalid registration details")
    else:
        form = UserRegisterForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    """
    Handles user login and authentication.

    Args:
        request (HttpRequest): The request object containing the login form data.
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if hasattr(user, 'userprofile') and user.userprofile.spotify_access_token:
                return redirect('profile')
            return redirect('spotify_login')
        messages.error(request, "Invalid username or password")
    return render(request, 'login.html')


def logout_view(request):
    """
    Logs the user out and clears the session.

    Args:
        request (HttpRequest): The request object.
    """
    logout(request)
    request.session.flush()
    return redirect('login')


def spotify_login(request):
    """
    Redirects the user to Spotify's authorization page.
    """
    client_id = settings.SPOTIFY_CLIENT_ID
    redirect_uri = 'http://localhost:8000/spotify/callback/'
    scope = SPOTIFY_SCOPE
    state = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')

    request.session['spotify_auth_state'] = state

    auth_url = (
        f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={client_id}"
        f"&scope={urllib.parse.quote(scope)}&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&state={state}"
    )
    return redirect(auth_url)


def spotify_callback(request):
    """
    Handles Spotify OAuth callback and token exchange.
    """
    code = request.GET.get('code')
    if not code:
        messages.error(request, "Authorization code not found.")
        return redirect('login')

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

    token_response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
    if token_response.status_code != 200:
        print(f"Token exchange failed: {token_response.content}")
        messages.error(request, "Failed to obtain access token.")
        return redirect('login')

    token_info = token_response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')  # in seconds
    expires_at = timezone.now() + timedelta(seconds=expires_in)

    headers = {'Authorization': f'Bearer {access_token}'}
    spotify_user_response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers, timeout=10)
    if spotify_user_response.status_code != 200:
        messages.error(request, "Failed to fetch Spotify user information.")
        return redirect('login')

    spotify_user_info = spotify_user_response.json()
    spotify_user_id = spotify_user_info['id']

    if request.user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_profile.spotify_user_id = spotify_user_id
        user_profile.spotify_access_token = access_token
        user_profile.spotify_refresh_token = refresh_token
        user_profile.token_expires_at = expires_at
        user_profile.save()

        messages.success(request, "Spotify account connected successfully.")
        return redirect('profile')
    messages.error(request, "You must be logged in to link your Spotify account.")
    return redirect('login')


@login_required
def wrapped_detail(request, wrap_id):
    """
    Displays the details of a specific Spotify wrap.
    """
    wrap = SpotifyWrap.objects.get(id=wrap_id, user_profile=request.user.userprofile)
    return render(request, 'wrapped_detail.html', {'wrap': wrap})


@login_required
def wrapped_presentation(request):
    """
    Fetches Spotify data and creates a wrap for the user.
    """
    user_profile = request.user.userprofile
    spotify_data = fetch_spotify_data(user_profile)

    if spotify_data:
        SpotifyWrap.objects.create(
            user_profile=user_profile,
            total_minutes_listened=spotify_data['recent_played'].get(
                'total', 0
            ),
            top_artists=", ".join(
                [artist['name'] for artist in spotify_data['top_artists']['items']]
            ),
            most_played_song=spotify_data['top_tracks']['items'][0]['name'] if spotify_data['top_tracks']['items'] else '',
            year=datetime.now().year
        )
    else:
        messages.error(request, "Failed to fetch Spotify data.")
        return redirect('profile')

    return render(request, 'wrapped_presentation.html', {'spotify_data': spotify_data})


@login_required
def profile_view(request):
    """
    Displays the user's profile with their past wraps.
    """
    wraps = SpotifyWrap.objects.filter(user=request.user)
    return render(request, 'profile.html', {'wraps': wraps})


@login_required
def past_wraps_view(request):
    """
    Displays the past Spotify wraps for the logged-in user.
    """
    wraps = SpotifyWrap.objects.filter(user=request.user)
    return render(request, 'wraps.html', {'wraps': wraps})


def contact_view(request):
    """
    Handles the contact form and sends an email.

    Args:
        request (HttpRequest): The request object containing the form data.
    """
    context = {}
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if subject and message:
            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.CONTACT_EMAIL])
                context['result'] = 'Email sent successfully'
            except Exception as e:
                context['result'] = f'Error sending email: {e}'
        else:
            context['result'] = 'All fields are required'
    return render(request, "contact.html", context)


@login_required
def delete_account(request):
    """
    Deletes the user's account and associated Spotify wraps.
    """
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
    """
    Deletes a specific Spotify wrap for the user.
    """
    wrap = SpotifyWrap.objects.get(id=wrap_id, user_profile=request.user.userprofile)
    wrap.delete()
    messages.success(request, "Wrap deleted successfully.")
    return redirect('profile')


def duo_wrapped(request, duo_id):
    """
    Displays the details of a duo Spotify wrap.
    """
    duo = DuoWrapped.objects.get(id=duo_id)
    return render(request, 'duo_wrapped.html', {'duo': duo})
