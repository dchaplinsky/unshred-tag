from urllib import quote_plus
from flask import url_for

from flask.ext.testing import TestCase

from models.user import User


class BasicTestCase(TestCase):
    def create_app(self):
        # siiiick, sick and stupid
        # We need to redefine some settings in weird way before import Flask
        # app because it got initialized on import. Yes, this is a little bit
        # stupid
        try:
            import local_settings as settings
        except ImportError:
            import settings

        settings.MONGODB_SETTINGS["DB"] = "unshred_test"
        settings.ENABLE_FIXTURES_ENDPOINTS = True
        import app as unshred
        return unshred.app

    def create_user_and_login(self, username="user"):
        self.client.post(url_for("fixtures.create_users"))
        self.client.post(url_for("fixtures.login_user", username=username))

    def is_user_logged(self):
        with self.client.session_transaction() as session:
            return "user_id" in session


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
