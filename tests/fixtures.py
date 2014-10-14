from flask import url_for

from models import Shreds, Tags, TaggingSpeed, User, Pages
from . import BasicTestCase


class FixturesTest(BasicTestCase):
    def setUp(self):
        self.client.post(url_for("fixtures.reset_db"))

    def assert_count(self, model, expected_count, **kwargs):
        self.assertEquals(model.objects(**kwargs).count(), expected_count)

    def assert_success(self, res):
        self.assert200(res)
        self.assertEquals(res.json, {"result": True})

    def test_reset_db(self):
        Shreds().save()
        Tags().save()
        TaggingSpeed().save()
        User().save()
        Pages().save()

        self.assert_count(Shreds, 1)
        self.assert_count(Tags, 1)
        self.assert_count(TaggingSpeed, 1)
        self.assert_count(User, 1)
        self.assert_count(Pages, 1)

        res = self.client.post(url_for("fixtures.reset_db"))
        self.assert_success(res)

        self.assert_count(Shreds, 0)
        self.assert_count(Tags, 0)
        self.assert_count(TaggingSpeed, 0)
        self.assert_count(User, 0)
        self.assert_count(Pages, 0)

    def test_import_base_tags(self):
        self.assert_count(Tags, 0)
        res = self.client.post(url_for("fixtures.create_base_tags"))
        self.assert_success(res)

        self.assert_count(Tags, 56)  # Magic number
        self.assert_count(Tags, 56, is_base=True)

    def test_import_users(self):
        self.assert_count(User, 0)
        res = self.client.post(url_for("fixtures.create_users"))
        self.assert_success(res)

        self.assert_count(User, 3)  # Nobody, User, Admin

    def test_import_shreds(self):
        self.assert_count(Shreds, 0)
        res = self.client.post(url_for("fixtures.create_shreds"))
        self.assert_success(res)

        self.assert_count(Shreds, 10)  # Another magic number
        self.assert_count(Shreds, 9, batch="fixtures")
        self.assert_count(Shreds, 0, batch="foobar")

    def login_user(self):
        self.client.post(url_for("fixtures.create_users"))

        for user in ["user", "admin"]:
            res = self.client.post(
                url_for("fixtures.login_user", username=user))
            self.assert_success(res)
            self.assertTrue(self.is_user_logged())

        for user in ["nobody"]:
            res = self.client.post(
                url_for("fixtures.login_user", username=user))
            self.assert_success(res)
            self.assertFalse(self.is_user_logged())
