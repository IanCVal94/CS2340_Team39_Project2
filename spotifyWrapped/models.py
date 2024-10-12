from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_minutes_watched = models.IntegerField(default=0)
    top_artists = models.TextField(blank=True, null=True)
    most_played_song = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField()

    class Meta:
        unique_together = ('user_profile', 'year')

class DuoWrapped(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    partner_username = models.CharField(max_length=150)
    total_duo_sessions = models.IntegerField(default=0)
    favorite_duo_song = models.CharField(max_length=255, blank=True, null=True)
    shared_minutes = models.IntegerField(default=0)

    def __str__(self):
        return f"Duo Wrapped: {self.user_profile.user.username} and {self.partner_username}"
