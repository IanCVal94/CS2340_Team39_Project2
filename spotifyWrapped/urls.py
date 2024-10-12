from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('wraps/<int:wrap_id>/', views.wrapped_detail, name='wrapped_detail'),
    path('duo/<int:duo_id>/', views.duo_wrapped, name='duo_wrapped'),
    path('contact/', views.contact_view, name='contact'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('delete_wrap/<int:wrap_id>/', views.delete_wrap, name='delete_wrap'),
    path('wraps/', views.past_wraps_view, name='wraps'),

    # Spotify OAuth URLs
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
]