"""
Models for user profiles and Spotify wrapped features.
"""
from django.contrib.auth.models import User
from django.db import models


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

    # Spotify related fields
    spotify_username = models.CharField(max_length=255, blank=True, null=True)
    spotify_user_id = models.CharField(max_length=255, blank=True, null=True)
    spotify_access_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.spotify_username
