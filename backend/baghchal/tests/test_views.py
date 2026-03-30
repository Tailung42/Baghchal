from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import User


class QuickMatchTestCase(TestCase):

    @classmethod
    def setUpClass(cls):

        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser", password="testpass")

    @patch("baghchal.views.async_get_all_games", return_value={"0000": {"status": "waiting", "player": {"goat": "", "tiger": "hero"}}})
    def test_quick_match_with_existing_game(self, *_):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # url = reverse("game/quick-match/")
        response = self.client.post("/game/quick-match/")
        self.assertEqual(response.data,{"game_id": "0000"})

    @patch("baghchal.views.async_get_all_games", return_value={"1111": {"status": "ongoing"}})
    @patch("baghchal.views.uuid.uuid4", return_value="0000")
    def test_quick_match_without_existing_game(self, *_):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        response = self.client.post("/game/quick-match/")
        self.assertEqual(response.data["game_id"], "0000")
