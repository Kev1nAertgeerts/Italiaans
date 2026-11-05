from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.template import engines
from django.urls import reverse

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class LoginViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", password="s3cret-pass!", phone="+32123456", email="a@example.com"
        )

    def test_get_login_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_invalid_credentials(self):
        response = self.client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_valid_credentials_log_in(self):
        response = self.client.post(reverse("login"), {"username": "alice", "password": "s3cret-pass!"})
        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_next_redirect_and_open_redirect_protection(self):
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "s3cret-pass!", "next": "/health/"},
        )
        self.assertRedirects(response, "/health/", fetch_redirect_response=False)
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "s3cret-pass!", "next": "https://evil.example/"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_required_redirects_to_login_url(self):
        @login_required
        def protected(request):
            return HttpResponse("ok")

        request = RequestFactory().get("/protected/")
        request.user = type("Anon", (), {"is_authenticated": False})()
        response = protected(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))


class CustomUserTests(TestCase):
    def test_custom_user_fields(self):
        user = User.objects.create_user(username="bob", password="x", phone="123")
        self.assertEqual(user.phone, "123")
        self.assertEqual(str(user), "bob")

    def test_context_processor_registered_and_renders(self):
        from django.conf import settings

        self.assertIn(
            "contexts_processors.global_context",
            settings.TEMPLATES[0]["OPTIONS"]["context_processors"],
        )
        request = RequestFactory().get("/")
        request.user = User.objects.create_user(username="carol", password="x")
        template = engines["django"].from_string("{{ user.username }}")
        self.assertEqual(template.render({}, request), "carol")
