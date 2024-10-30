"""
Views for handling user authentication, Spotify integration, and app functionality.
"""
import os
import time
import base64
import urllib.parse
from datetime import datetime, timedelta

import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail

from .models import UserProfile
from .utils import refresh_spotify_token
from .utils import get_spotify_auth_headers


# Spotify OAuth Constants
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
SPOTIFY_SCOPE = 'user-top-read user-read-recently-played'

def index(request):
    """
    Renders the index page.
    """
    return render(request, 'index.html')

def login_view(request):
    """
    Handles user login and authentication.

    Args:
        request (HttpRequest): The request object containing the login form data.
    """
    return spotify_login(request)
    # if request.method == 'POST':
    #     return redirect('spotify_login')
    # return render(request, 'login.html')


def logout_view(request):
    """
    Logs the user out and clears the session.

    Args:
        request (HttpRequest): The request object.
    """
    logout(request)
    request.session.flush()

    return redirect('index')


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
        return redirect('index')

    headers, data = get_spotify_auth_headers()
    data.update({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8000/spotify/callback/'
    })

    token_response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
    if token_response.status_code != 200:
        messages.error(request, "Failed to obtain access token.")
        return redirect('index')

    token_info = token_response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')
    expires_at = timezone.now() + timedelta(seconds=expires_in)

    headers = {'Authorization': f'Bearer {access_token}'}
    spotify_user_response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers, timeout=10)
    if spotify_user_response.status_code != 200:
        messages.error(request, "Failed to fetch Spotify user information.")
        return redirect('index')

    spotify_user_info = spotify_user_response.json()
    print(spotify_user_info)
    spotify_user_id = spotify_user_info['id']
    spotify_username = spotify_user_info.get('display_name', spotify_user_id)
    internal_email = f'{spotify_user_id}@spotify.com'

    user, created = User.objects.get_or_create(
        email=internal_email,
        defaults={'username': spotify_username}
    )

    if created:
        user.email = internal_email
        user.save()

    login(request, user)  # Log the user in

    # Create or update user profile using Spotify details
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_profile.spotify_username = spotify_username
    user_profile.spotify_user_id = spotify_user_id
    user_profile.spotify_access_token = access_token
    user_profile.spotify_refresh_token = refresh_token
    user_profile.token_expires_at = expires_at
    user_profile.save()

    messages.success(request, f"Logged in as {spotify_username}")

    return redirect('profile')


@login_required
def profile_view(request):
    """
    Displays the user's profile with their past wraps.
    """
    print(request.user)
    user_profile = None
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    else:
        messages.error(request, "No userprofile attribute")

    return render(request, 'profile.html', {'user_profile': user_profile})


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


def wraps_view(request):
    user_profile = None
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    else:
        messages.error(request, "No userprofile attribute")
    token = user_profile.spotify_access_token
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Base URL for Spotify's top tracks endpoint
    base_url = "https://api.spotify.com/v1/me/top/tracks?limit=50"

    # Get short-term top tracks
    short_term_url = f"{base_url}&time_range=short_term"
    response_short = requests.get(short_term_url, headers=headers)
    short_term_tracks = response_short.json()

    # Get medium-term top tracks
    medium_term_url = f"{base_url}&time_range=medium_term"
    response_medium = requests.get(medium_term_url, headers=headers)
    medium_term_tracks = response_medium.json()

    # Get long-term top tracks
    long_term_url = f"{base_url}&time_range=long_term"
    response_long = requests.get(long_term_url, headers=headers)
    long_term_tracks = response_long.json()

    current_time_ms = int(time.time() * 1000)

    # Calculate the 'after' timestamp, which is 5 minutes (300,000 ms) ago
    five_minutes_ago_ms = current_time_ms - 300000

    # Set up the request URL
    recently_played_url = f"https://api.spotify.com/v1/me/player/recently-played?limit=50&after={five_minutes_ago_ms}"
    recent_response = requests.get(recently_played_url, headers=headers)
    recent_tracks = recent_response.json()

    # Print results or process them as needed
    print(recent_tracks)
    print("Short-term Top Tracks:", short_term_tracks)
    print("Medium-term Top Tracks:", medium_term_tracks)
    print("Long-term Top Tracks:", long_term_tracks)

    # Assume short_term_tracks is the JSON response containing the list of top tracks
    top_5_short_term = short_term_tracks.get('items', [])[:5]  # Get the first 5 tracks

    # Format and print the top 5 tracks
    print("Top 5 Short-term Tracks:")
    for i, track in enumerate(top_5_short_term, start=1):
        track_name = track['name']
        artists = ', '.join(artist['name'] for artist in track['artists'])
        print(f"{i}. {track_name} by {artists}")


    # Display the results or use them as needed


    return render(request, 'wraps.html', {'user_profile': user_profile, 'wraps': short_term_tracks})
