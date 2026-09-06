from unittest.mock import patch

from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from django.urls import include, path

from core.models import User


class _BaghchalURLConf:
    urlpatterns = [path("game/", include("baghchal.urls"))]


class QuickMatchTestCase(TransactionTestCase):
    databases = ["default"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser", password="testpass")

    def setUp(self):
        from rest_framework.test import APIClient

        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _override_root_urls(self):
        from django.urls import include, path

        class _IncludedBaghchalURLConf:
            urlpatterns = [path("game/", include("baghchal.urls"))]

        return _IncludedBaghchalURLConf

    def test_quick_match_with_existing_game(self):
        from unittest.mock import patch

        with patch("baghchal.persistence.views._get_all_games", return_value={"0000": {"status": "waiting", "player": {"goat": "", "tiger": "hero"}}}):
            with self.settings(ROOT_URLCONF=self._override_root_urls()):
                response = self.client.post("/game/quick-match/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"game_id": "0000"})

    def test_quick_match_without_existing_game(self):
        from unittest.mock import patch

        with patch("baghchal.persistence.views._get_all_games", return_value={}):
            with patch("baghchal.persistence.views.uuid.uuid4", return_value="0000"):
                with self.settings(ROOT_URLCONF=self._override_root_urls()):
                    response = self.client.post("/game/quick-match/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["game_id"], "0000")
