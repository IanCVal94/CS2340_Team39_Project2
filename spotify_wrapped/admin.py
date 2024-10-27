"""
Admin configuration for Spotify Wrapped models.
"""
from django.contrib import admin
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model, displaying user-related fields.
    """
    list_display = ('bio', 'profile_picture', 'favorite_genres', 'created_at')


# Register the models with the admin site
admin.site.register(UserProfile, UserProfileAdmin)