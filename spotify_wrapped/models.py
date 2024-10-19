"""
Models for user profiles and Spotify wrapped features.
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Model to store additional user profile information,
    including Spotify authentication tokens and preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    favorite_genres = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Spotify related fields
    spotify_user_id = models.CharField(max_length=255, blank=True, null=True)
    spotify_access_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class SpotifyWrap(models.Model):
    """
    Model to store the user's Spotify wrapped data for a particular year.
    This includes their top artists, most played song, and total listening time.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_minutes_listened = models.IntegerField(default=0)
    top_artists = models.TextField(blank=True, null=True)
    most_played_song = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'year'], name='unique_spotify_wrap_per_year')
        ]

    def __str__(self):
        return f"{self.user.username}'s Spotify Wrapped {self.year}"


class DuoWrapped(models.Model):
    """
    Model to store information about a user's shared listening experience
    with another user (partner) through the Duo feature.
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    partner_username = models.CharField(max_length=150)
    total_duo_sessions = models.IntegerField(default=0)
    favorite_duo_song = models.CharField(max_length=255, blank=True, null=True)
    shared_minutes = models.IntegerField(default=0)

    def __str__(self):
        return f"Duo Wrapped: {self.user_profile.user.username} and {self.partner_username}"
