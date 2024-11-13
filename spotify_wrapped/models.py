"""
Models for user profiles and Spotify wrapped features.
"""
from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import ArrayField


class UserProfile(models.Model):
    """
    Model to store additional user profile information,
    including Spotify authentication tokens and preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile', null=True, blank=True)

    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    favorite_genres = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=255, blank=True, null=True)
    # Spotify related fields
    spotify_username = models.CharField(max_length=255, blank=True, null=True)
    spotify_user_id = models.CharField(max_length=255, blank=True, null=True)
    spotify_access_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.spotify_username


class SpotifyWraps(models.Model):
    """
    Model to store individual spotify wrapped information for a single wrap
    Each wrap has a top songs, top artists, and top genres that would all be present for the designated wrap
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='saved_wraps')
    top_songs = ArrayField(models.TextField(), blank=True, default=list)
    date_time = models.DateTimeField(auto_now_add=True)
    length = models.CharField(max_length=255, blank=True, null=True)
    top_artists = ArrayField(models.TextField(), blank=True, default=list)
    top_genres = ArrayField(models.TextField(), blank=True, default=list)
    last_5_tracks = ArrayField(models.TextField(), blank=True, default=list)
    last_5_artists = ArrayField(models.TextField(), blank=True, default=list)
    num_distinct_artists = models.SmallIntegerField(blank=True, null=True)
    num_genres = models.SmallIntegerField(blank=True, null=True)


