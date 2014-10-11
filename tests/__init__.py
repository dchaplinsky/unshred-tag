from flask import url_for
from flask.ext.testing import TestCase


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
