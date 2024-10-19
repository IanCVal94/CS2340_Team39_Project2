"""
Admin configuration for Spotify Wrapped models.
"""
from django.contrib import admin
from .models import UserProfile, SpotifyWrap, DuoWrapped


class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model, displaying user-related fields.
    """
    list_display = ('user', 'bio', 'profile_picture', 'favorite_genres', 'created_at')


class SpotifyWrapAdmin(admin.ModelAdmin):
    """
    Admin interface for the SpotifyWrap model, displaying wrap-related fields.
    """
    list_display = ('user', 'total_minutes_listened', 'top_artists', 'most_played_song', 'year')


class DuoWrappedAdmin(admin.ModelAdmin):
    """
    Admin interface for the DuoWrapped model, displaying duo session-related fields.
    """
    list_display = (
        'user_profile', 'partner_username', 'total_duo_sessions', 
        'favorite_duo_song', 'shared_minutes'
    )


# Register the models with the admin site
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(SpotifyWrap, SpotifyWrapAdmin)
admin.site.register(DuoWrapped, DuoWrappedAdmin)
