from django.contrib import admin
from .models import UserProfile, SpotifyWrap, DuoWrapped

# Register the models
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture', 'favorite_genres', 'created_at')

class SpotifyWrapAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_minutes_listened', 'top_artists', 'most_played_song', 'year')

class DuoWrappedAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'partner_username', 'total_duo_sessions', 'favorite_duo_song', 'shared_minutes')


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(SpotifyWrap, SpotifyWrapAdmin)
admin.site.register(DuoWrapped, DuoWrappedAdmin)