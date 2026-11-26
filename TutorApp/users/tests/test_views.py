from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from users.tests.factories import UserFactory

User = get_user_model()


class UserRegisterViewTests(TestCase):
    def setUp(self):
        self.url = reverse("users:register")

    def test_register_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post_valid(self):
        data = {
            "username": "newuser",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "email": "newuser@example.com",
            "school_type": "SECONDARY",
        }
        response = self.client.post(self.url, data, follow=True)

        self.assertRedirects(response, reverse("users:login"))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.role_type, 1)

        actual_messages = [m.message for m in list(response.context["messages"])]
        self.assertIn("Account has been created. You can now log in.", actual_messages)

    def test_register_view_post_invalid(self):
        data = {
            "username": "newuser",
            "password1": "weak",
            "password2": "notmatching",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, "form", "password2", "The two password fields didn’t match."
        )
        self.assertEqual(User.objects.count(), 0)

        actual_messages = [m.message for m in list(response.context["messages"])]
        self.assertIn(
            "There was an error creating your account. Please correct the form below.",
            actual_messages,
        )


class LoginViewTests(TestCase):
    def setUp(self):
        self.url = reverse("users:login")
        self.home_url = reverse("users:home")
        self.password = "StrongPassword123!"
        self.user = UserFactory(password=self.password)

    def test_login_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_view_authenticated_redirects(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.url)
        self.assertRedirects(response, "/")

    def test_login_success(self):
        data = {
            "username": self.user.username,
            "password": self.password,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/")

    def test_login_failure(self):
        data = {
            "username": self.user.username,
            "password": "wrongpassword",
        }
        response = self.client.post(self.url, data)
        self.assertContains(response, "Invalid username or password.")
        self.assertEqual(response.status_code, 200)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.url = reverse("users:logout")
        self.password = "StrongPassword123!"
        self.user = UserFactory(password=self.password)

    def test_logout(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("login"))
        self.assertFalse("_auth_user_id" in self.client.session)


class HomeViewTests(TestCase):
    def setUp(self):
        self.url = reverse("users:home")
        self.user = UserFactory()

    def test_home_view_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)
