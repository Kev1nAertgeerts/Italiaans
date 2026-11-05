from django.test import TestCase, override_settings


@override_settings(SECURE_SSL_REDIRECT=False)
class CoreViewTests(TestCase):
    def test_home(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_health(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
