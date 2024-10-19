"""
Configuration for the Spotify Wrapped app.
"""
from django.apps import AppConfig


class SpotifyWrappedConfig(AppConfig):
    """
    Configuration class for the Spotify Wrapped app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spotify_wrapped'
