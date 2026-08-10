from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    def test_api_root_returns_json(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Welcome to AutoACE Audio Analysis API"},
        )
