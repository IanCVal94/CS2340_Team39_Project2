"""
This module contains unit tests for the UserProfile and SpotifyWraps models.
It validates the creation of these models, their relationships, and key functionality.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, SpotifyWraps
import json

class UserProfileTests(TestCase):
    """
    Unit tests for the UserProfile model. This model is responsible for storing
    additional user profile information, such as Spotify authentication details
    and user preferences.
    """

    def setUp(self):
        """
        Sets up a dummy User and UserProfile instance for testing.
        This method is called before every test case in this class.
        """
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            bio="This is a test bio",
            favorite_genres="pop, rock",
            spotify_username="test_spotify_user",
        )

    def test_user_profile_creation(self):
        """
        Tests the creation of a UserProfile and ensures the fields are populated
        correctly.
        """
        self.assertEqual(self.user_profile.user.username, "testuser")
        self.assertEqual(self.user_profile.bio, "This is a test bio")

    def test_user_profile_str_method(self):
        """
        Tests that the __str__ method of the UserProfile model returns the expected
        Spotify username.
        """
        self.assertEqual(str(self.user_profile), "test_spotify_user")


class SpotifyWrapsTests(TestCase):
    """
    Unit tests for the SpotifyWraps model. This model stores Spotify wrapped data,
    including top songs, top artists, and other metrics for individual users.
    """

    def setUp(self):
        """
        Sets up a dummy User, UserProfile, and SpotifyWrap instance for testing.
        This method is called before every test case in this class.
        """
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.user_profile = UserProfile.objects.create(user=self.user, spotify_username="test_spotify_user")
        self.spotify_wrap = SpotifyWraps.objects.create(
            user_profile=self.user_profile,
            top_songs=json.dumps(["Song1", "Song2", "Song3"]),
            top_artists=json.dumps(["Artist1", "Artist2"]),
            top_genres=json.dumps(["Genre1", "Genre2"]),
            num_distinct_artists=2,
            num_genres=2,
        )

    def test_spotify_wrap_creation(self):
        """
        Tests the creation of a SpotifyWrap and ensures the fields are populated
        correctly with valid data.
        """
        self.assertEqual(json.loads(self.spotify_wrap.top_songs), ["Song1", "Song2", "Song3"])
        self.assertEqual(self.spotify_wrap.num_distinct_artists, 2)
        self.assertEqual(self.spotify_wrap.num_genres, 2)

    def test_spotify_wrap_relationship(self):
        """
        Tests the relationship between SpotifyWrap and UserProfile, ensuring
        the SpotifyWrap is linked to the correct UserProfile.
        """
        self.assertEqual(self.spotify_wrap.user_profile.spotify_username, "test_spotify_user")