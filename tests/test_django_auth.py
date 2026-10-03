from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings

from consultas.views import biometric_list


@override_settings(ALLOWED_HOSTS=["testserver"])
class AuthenticationTests(SimpleTestCase):
    def test_biometric_list_redirects_anonymous_users_to_login(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        response = biometric_list(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/accounts/login/?next=/")
