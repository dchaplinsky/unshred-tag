from flask import url_for

from models import Tags
from . import BasicTestCase


class TaggingTest(BasicTestCase):
    def setUp(self):
        self.client.post(url_for("fixtures.reset_db"))
        self.client.post(url_for("fixtures.create_base_tags"))

    def test_index_not_logged(self):
        res = self.client.get(url_for("index"))

        self.assert200(res)
        body = res.get_data(as_text=True)
        self.assertTrue("warm-welcome" in body)
        self.assertTrue(url_for("social.auth", backend="facebook") in body)
        self.assertTrue(url_for("social.auth", backend="twitter") in body)
        self.assertTrue(
            url_for("social.auth", backend="google-oauth2") in body)
        self.assertTrue(
            url_for("social.auth", backend="vk-oauth2") in body)

    def test_index_logged(self):
        self.create_user_and_login("user")

        res = self.client.get(url_for("index"))

        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertFalse("warm-welcome" in body)
        self.assertFalse(url_for("social.auth", backend="facebook") in body)
        self.assertFalse(url_for("social.auth", backend="twitter") in body)
        self.assertFalse(
            url_for("social.auth", backend="google-oauth2") in body)
        self.assertFalse(
            url_for("social.auth", backend="vk-oauth2") in body)

        for tag in Tags.objects(is_base=True):
            self.assertTrue(tag.title.lower() in body.lower())
            self.assertTrue(tag.category.lower() in body.lower())
            if tag.hotkey:
                self.assertTrue(tag.hotkey in body.lower())

    def test_no_more_tasks(self):
        self.create_user_and_login("user")

        res = self.client.get(url_for("next"))

        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertFalse("shred_id" in body)
        self.assertFalse(url_for("next") in body)

    def test_has_some_tasks(self):
        self.create_user_and_login("user")

        self.client.post(url_for("fixtures.create_shreds"))

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertTrue("shred_id" in body)
        self.assertTrue(url_for("next") in body)

        for tag in Tags.objects(is_base=True):
            self.assertTrue(
                tag.title.capitalize().encode('unicode-escape') in body)
