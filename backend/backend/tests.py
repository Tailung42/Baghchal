from django.test import TestCase
from django.urls import reverse

class HealthCheckTests(TestCase):
    def test_health_check_endpoint(self):
        url = reverse('health_check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
