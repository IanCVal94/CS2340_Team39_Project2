"""
URL configuration for handling app views and Spotify OAuth routes.
"""
from django.urls import path
from django.conf.urls.i18n import set_language
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('wraps/', views.wraps_view, name='wraps'),
    path('wrap_base/', views.wrap_base, name='wrap_base'),
    path('wrap1/', views.wrap1, name='wrap1'),
    path('wrap2/', views.wrap2, name='wrap2'),
    path('wrap3/', views.wrap3, name='wrap3'),
    path('wrap4/', views.wrap4, name='wrap4'),
    path('wrap5/', views.wrap5, name='wrap5'),
    path('wrap6/', views.wrap6, name='wrap6'),
    path('wrap7/', views.wrap7, name='wrap7'),
    path('logout/', views.logout_view, name='logout'),
    path('contact/', views.contact_view, name='contact'),
    path('settings/', views.settings_view, name='settings'),
    # Spotify OAuth URLs
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('set_language/', set_language, name='set_language'),

]
