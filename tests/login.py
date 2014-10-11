from urllib import quote_plus

from flask import url_for

from models.user import User
from . import BasicTestCase


class LoginTest(BasicTestCase):
    def test_inactive_user_login(self):
        self.create_user_and_login(username="nobody")
        self.assertFalse(self.is_user_logged())

    def test_logout(self):
        self.assertFalse(self.is_user_logged())
        self.create_user_and_login()
        self.assertTrue(self.is_user_logged())

        response = self.client.get(url_for("logout"))
        self.assert405(response)
        self.assertTrue(self.is_user_logged())

        response = self.client.post(
            url_for("logout"), follow_redirects=True)

        self.assert200(response)
        self.assertFalse(self.is_user_logged())

    def test_protected_endpoints(self):
        for url in ["next", "review", "pages"]:
            response = self.client.get(url_for(url))
            self.assert_redirects(response, "%s?next=%s" % (
                url_for("index"), quote_plus(url_for(url))))

    def tearDown(self):
        User.objects().delete()
