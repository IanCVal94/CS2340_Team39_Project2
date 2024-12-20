"""
Views for handling user authentication, Spotify integration, and app functionality.
"""
import collections
import os
import base64
import urllib.parse
from datetime import timedelta
import json

import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.utils import timezone
from django.core.mail import send_mail
from openai import OpenAI

from .models import UserProfile, SpotifyWraps
from .utils import get_spotify_auth_headers



# Spotify OAuth Constants
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'
SPOTIFY_SCOPE = 'user-top-read user-read-recently-played'

session = requests.Session()
session.verify = False

def index(request):
    """
    Renders the homepage of the application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered homepage.
    """

    context = None
    if request.user.is_authenticated:
        context = {'spotify_username': request.user.userprofile.spotify_username}
    return render(request, 'index.html', context)

def wrap_base(request):
    """
    Renders the wrap_base page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap_base page.
    """
    return render(request, 'wrap_base.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap1(request):
    """
    Renders the wrap1 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap1 page.
    """
    return render(request, 'wrap1.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap2(request):
    """
    Renders the wrap2 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap2 page.
    """
    return render(request, 'wrap2.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap3(request):
    """
    Renders the wrap3 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap3 page.
    """
    return render(request, 'wrap3.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap4(request):
    """
    Renders the wrap4 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap4 page.
    """
    return render(request, 'wrap4.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap5(request):
    """
    Renders the wrap5 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap5 page.
    """
    return render(request, 'wrap5.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap6(request):
    """
    Renders the wrap6 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap6 page.
    """
    return render(request, 'wrap6.html', {'spotify_username': request.user.userprofile.spotify_username})

def wrap7(request):
    """
    Renders the wrap7 page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wrap7 page.
    """
    return render(request, 'wrap7.html', {'spotify_username': request.user.userprofile.spotify_username})

def login_view(request):
    """
    Handles user login and authentication by redirecting to Spotify login.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered spotify_login page.
    """
    return spotify_login(request)


def logout_view(request):
    """
    Logs the user out by clearing session data and redirecting to a logout page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered logout page.
    """
    # Clear Spotify session tokens
    if 'spotify_access_token' in request.session:
        del request.session['spotify_access_token']
    if 'spotify_refresh_token' in request.session:
        del request.session['spotify_refresh_token']

    # Log the user out locally
    logout(request)
    request.session.flush()

    return render(request, 'logout_redirect.html')

def spotify_login(request):
    """
    Redirects the user to Spotify's OAuth authorization page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponseRedirect: Redirect to Spotify's authorization page.
    """
    client_id = settings.SPOTIFY_CLIENT_ID
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    scope = SPOTIFY_SCOPE
    state = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')

    request.session['spotify_auth_state'] = state

    auth_url = (
        f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={client_id}"
        f"&scope={urllib.parse.quote(scope)}&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&state={state}"
    )
    return redirect(auth_url)

def fetch_spotify_token(data, headers):
    """
    Fetches Spotify tokens using the provided data and headers.

    Args:
        data (HttpRequest): spotify data.
        headers (HttpRequest): spotify headers.

    Returns:
        response: spotify response info in json format.
    """
    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()

def fetch_spotify_user_info(access_token):
    """
    Fetches Spotify user information using the access token.

    Args:
        access_token (HttpRequest): spotify access token.

    Returns:
        response: spotify response info in json format.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()

def spotify_callback(request):
    """
    Handles Spotify's OAuth callback to exchange a code for access and refresh tokens.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponseRedirect: Redirect to the user's profile upon successful login.
    """
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    code = request.GET.get('code')
    if not code:
        messages.error(request, "Authorization code not found.")
        return redirect('index')

    headers, data = get_spotify_auth_headers()
    data.update({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    })

    token_info = fetch_spotify_token(data, headers)
    if not token_info:
        messages.error(request, "Failed to obtain access token.")
        return redirect('index')

    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')
    expires_at = timezone.now() + timedelta(seconds=expires_in)

    spotify_user_info = fetch_spotify_user_info(token_info.get('access_token'))
    if not spotify_user_info:
        messages.error(request, "Failed to fetch Spotify user information.")
        return redirect('index')

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

    login(request, user)

    # Create or update user profile using Spotify details
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_profile.spotify_username = spotify_username
    user_profile.spotify_user_id = spotify_user_id
    user_profile.spotify_access_token = access_token
    user_profile.spotify_refresh_token = refresh_token
    user_profile.token_expires_at = expires_at
    user_profile.save()

    messages.success(request, f"Logged in as {spotify_username}")

    return redirect('index')

def contact_view(request):
    """
    Handles the contact form submissions and sends an email.

    Args:
        request (HttpRequest): The request object containing form data.

    Returns:
        HttpResponse: Rendered contact page with success or error message.
    """
    context = {}
    if request.user.is_authenticated:
        context = {'spotify_username': request.user.userprofile.spotify_username}
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

def settings_view(request):
    """
    Renders the settings page for the user's profile.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered settings page.
    """
    return render(request, "settings.html", {'spotify_username': request.user.userprofile.spotify_username})

def wraps_view(request):
    """
    Displays all Spotify wraps associated with the logged-in user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wraps page with all wraps.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    token = user_profile.spotify_access_token

    # Fetch saved wraps for the current user
    wraps = SpotifyWraps.objects.filter(user_profile=user_profile).order_by("-date_time")
    return render(request, 'wraps.html', {'all_wraps': wraps, 'spotify_username': request.user.userprofile.spotify_username})

def delete_wrap(request, wrap_id):
    """
    Deletes a specific Spotify wrap associated with the logged-in user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered wraps page with deleting the specific wrap.
    """
    try:
        wrap = SpotifyWraps.objects.get(id=wrap_id, user_profile__user=request.user)
        wrap.delete()
        return JsonResponse({"message": "Wrap deleted successfully."})
    except SpotifyWraps.DoesNotExist:
        return JsonResponse({"error": "Wrap not found."}, status=404)


def view_wrap(request, page_num=0, wrap_id=-1):
    """
    Views a specific Spotify wrap associated with the logged-in user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered the specific wrap presentation slides.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    timeframe = request.GET.get("timeframe")
    # wrap_id = request.GET.get("wrap_id")

    if wrap_id != -1:
        try:
            wrap = SpotifyWraps.objects.get(id=wrap_id, user_profile=user_profile)
        except SpotifyWraps.DoesNotExist:
            messages.error(request, "Wrap not found.")
            return redirect('wraps_view')
    elif timeframe:
        # Create a new wrap for the specified timeframe
        wrap = create_wrap_for_timeframe(user_profile, timeframe)
    else:
        messages.error(request, "Invalid request.")
        return redirect('wraps_view')

    # Prepare context
    context = {
        'spotify_username': request.user.userprofile.spotify_username,
        'length': wrap.length,
        'date_time': wrap.date_time,
        'top_songs': json.loads(wrap.top_songs),
        'top_artists': json.loads(wrap.top_artists),
        'top_genres': json.loads(wrap.top_genres),
        'num_distinct_artists': wrap.num_distinct_artists,
        'num_genres': wrap.num_genres,
        'wrap_index': page_num,
        'wrap_num': wrap.id,
        'wrap_LLM_en': wrap.LLM_description_en,
        'wrap_LLM_az': wrap.LLM_description_az,
        'wrap_LLM_ru': wrap.LLM_description_ru,
    }



    # Templates for wrap pages
    wrap_templates = [
        'wrap_base.html',
        'wrap1.html',
        'wrap2.html',
        'wrap3.html',
        'wrap4.html',
        'wrap5.html',
        'wrap6.html',
        'wrap7.html',
    ]
    template = wrap_templates[page_num]

    return TemplateResponse(request, template, context)


def create_wrap_for_timeframe(user_profile, timeframe):
    """
    Creates a new Spotify wrap for a given timeframe by fetching top songs,
    artists, and genres from the Spotify API.

    Args:
        user_profile (UserProfile): The user's profile.
        timeframe (str): The time range for the wrap.

    Returns:
        SpotifyWraps: The created wrap object.
    """
    token = user_profile.spotify_access_token
    headers = {'Authorization': f'Bearer {token}'}
    time_mapping = {
        "1 month": "short_term",
        "1 year": "medium_term",
        "5 years": "long_term",
    }
    time_range = time_mapping.get(timeframe, "short_term")

    # Fetch data from Spotify API
    base_url_tracks = "https://api.spotify.com/v1/me/top/tracks?limit=50"
    response_tracks = requests.get(f"{base_url_tracks}&time_range={time_range}", headers=headers)
    tracks_data = response_tracks.json()

    base_url_artists = "https://api.spotify.com/v1/me/top/artists?limit=50"
    response_artists = requests.get(f"{base_url_artists}&time_range={time_range}", headers=headers)
    artists_data = response_artists.json()

    # Extract top songs, artists, and genres
    top_songs = [track.get("name", "None (Spotify was not used)") for track in tracks_data.get("items", [])[:5]]
    top_artists = [artist.get("name", "None (Spotify was not used)") for artist in artists_data.get("items", [])[:5]]

    all_genres = []
    for artist in artists_data.get("items", []):
        all_genres.extend(artist.get("genres", []))

    # Count occurrences of each genre
    genre_counter = collections.Counter(all_genres)

    # Get the top 5 genres, or use fallback if empty
    top_genres = [genre for genre, count in genre_counter.most_common(5)]
    if not top_genres:
        top_genres = ["Unfortunately, due to stricter spotify API restrictions, we can no longer show this :("]

    # Ensure fallback for any empty sections
    if not top_songs:
        top_songs = ["None (Spotify was not used during the time interval selected)"]
    if not top_artists:
        top_artists = ["Unfortunately, due to stricter spotify API restrictions, we can no longer show this :("]

    num_distinct_artists = len(set(artist for artist in top_artists if artist != "None (Spotify was not used)"))
    num_genres = len(set(top_genres)) if top_genres[0] != "None (Spotify was not used)" else 0
    api_key = settings.OPENAI_KEY_SECRET
    message_template = [
        {
            "role": "system",
            "content": "You are a person who knows all about this other person's spotify data"
        },
        {
            "role": "user",
            "content": (
                f"Write exactly what that person would think, act and tell exact clothing from top to bottom that they would wear like using that spotify wrapped data, in 60 words or less:\n\n"
                f"Top Songs: {', '.join(top_songs)}\n"
                f"Top Artists: {', '.join(top_artists)}\n"
                f"Top Genres: {', '.join(top_genres)}\n"
                f"Number of Distinct Artists: {num_distinct_artists}\n"
                f"Number of Genres: {num_genres}\n"
            ),
        }
    ]

    client = OpenAI(api_key=api_key)
    translations = {}
    languages = {
        "en": "English",
        "az": "Azerbaijani",
        "ru": "Russian"
    }

    for lang in languages:
        translated_message = message_template.copy()
        if lang != "en":
            translated_message[-1]["content"] += f" and write it in {languages[lang]}."

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=translated_message,
            temperature=0.7,
            max_tokens=100,
        )
        translations[lang] = response.choices[0].message.content.strip()
    print(f"Created wrap: {translations["en"]}")
    print(f"Created wrap: {translations["az"]}")
    print(f"Created wrap: {translations["ru"]}")
    # Save wrap
    wrap = SpotifyWraps.objects.create(
        user_profile=user_profile,
        top_songs=json.dumps(top_songs),
        top_artists=json.dumps(top_artists),
        top_genres=json.dumps(top_genres),
        length=timeframe,
        num_distinct_artists=num_distinct_artists,
        num_genres=num_genres,
        LLM_description_en=translations["en"],
        LLM_description_az=translations["az"],
        LLM_description_ru=translations["ru"]
    )
    print(f"Created wrap: {wrap}")
    return wrap

def delete_account(request):
    """
    Deletes all wraps associated with the logged-in user's account and logs them out.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered home page.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        # Delete all wraps for the user's profile
        SpotifyWraps.objects.filter(user_profile=user_profile).delete()

        # Log the user out
        logout(request)
        messages.success(request, "Your account data has been deleted, and you have been logged out.")

        # Redirect to the homepage
        return redirect('index')
    except UserProfile.DoesNotExist:
        messages.error(request, "No account data found to delete.")
        return redirect('settings_view')

def set_theme(request, theme_name):
    """
    Updates the user's selected theme and stores it in the session.

    This function allows users to change the appearance of the application
    by selecting a predefined theme. The selected theme is stored in the session
    and applied across the application.

    Args:
        request (HttpRequest): The HTTP request object that includes session data.
        theme_name (str): The name of the theme to be applied. Must be one of
                          ['holiday', 'dark', 'light'].

    Returns:
        HttpResponseRedirect: Redirects the user to the 'index' page after
                              updating the theme.
    """
    if theme_name in ['holiday', 'dark', 'light']:
        request.session['theme'] = theme_name
    return redirect('index')