import re
from datetime import datetime
from flask import url_for

from models import Cluster, Tags, User, TaggingSpeed, Shred
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

        self.assertTrue("item_id" in body)
        self.assertTrue(url_for("next") in body)

        for tag in Tags.objects(is_base=True):
            self.assertTrue(
                tag.title.capitalize().encode('unicode-escape') in body)

    def test_user_tags_in_task(self):
        self.create_user_and_login("user")

        self.client.post(url_for("fixtures.create_shreds"))

        user = User.objects.get(username="user")
        admin = User.objects.get(username="admin")
        user_tag = "foobar"
        another_user_tag = "barfoo"

        Tags.objects.create(title=user_tag, is_base=False,
                            created_by=user)
        Tags.objects.create(title=another_user_tag, is_base=False,
                            created_by=admin)

        user.tags = [user_tag]
        admin.tags = [another_user_tag]
        user.save()
        admin.save()

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertTrue(
            user_tag.capitalize().encode('unicode-escape') in body)
        pos = body.index(user_tag.capitalize().encode('unicode-escape'))

        self.assertFalse(
            another_user_tag.capitalize().encode('unicode-escape') in body)

        for tag in Tags.objects(is_base=True):
            tag = tag.title.capitalize().encode('unicode-escape')
            self.assertTrue(tag in body)

            self.assertTrue(body.index(tag) < pos)

    def test_tags_ordering_in_task(self):
        self.create_user_and_login("user")
        self.client.post(url_for("fixtures.create_shreds"))

        first_tag = Tags.objects[0]
        new_first_tag = Tags.objects[1]

        new_first_tag.usages = 100
        new_first_tag.save()

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertTrue(
            body.index(first_tag.title.capitalize().encode('unicode-escape')) >
            body.index(
                new_first_tag.title.capitalize().encode('unicode-escape'))
        )

    def test_auto_tags(self):
        self.create_user_and_login("user")
        self.client.post(url_for("fixtures.create_shreds"))

        tag = Tags.objects.create(title="my new tag",
                                  synonyms=["foobar_synonym"],
                                  is_base=True)

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertEquals(
            body.count(tag.title.capitalize().encode('unicode-escape')), 1)

        Shred.objects.update(add_to_set__tags=["foobar_synonym"])

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        self.assertEquals(
            body.count(tag.title.capitalize().encode('unicode-escape')), 2)

    def parse_shred_id(self, body):
        pattern = r'id="item_id".*?"([^"]*)"'

        m = re.search(pattern, body)
        return m.group(1)

    def test_skipping(self):
        self.create_user_and_login("user")
        user = User.objects.get(username="user")
        self.assertEqual(user.skipped, 0)
        self.assertEqual(user.processed, 0)

        self.client.post(url_for("fixtures.create_shreds"))

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        current_shred_id = first_shred_id = self.parse_shred_id(body)
        seen_shreds = {current_shred_id}

        for i in xrange(9):
            res = self.client.post(url_for("skip"),
                                   data={"_id": current_shred_id},
                                   follow_redirects=True)

            body = res.get_data(as_text=True)
            self.assert200(res)

            current_shred_id = self.parse_shred_id(body)
            self.assertNotIn(current_shred_id, seen_shreds)
            seen_shreds.add(current_shred_id)

        self.assertEqual(
            len(Cluster.objects(id=first_shred_id).first().users_skipped), 1)

        res = self.client.post(url_for("skip"),
                               data={"_id": current_shred_id},
                               follow_redirects=True)

        body = res.get_data(as_text=True)
        self.assert200(res)

        current_shred_id = self.parse_shred_id(body)
        self.assertIn(current_shred_id, seen_shreds)

        self.assertEqual(
            len(Cluster.objects(id=current_shred_id).first().users_skipped), 0)

        user.reload()
        self.assertEqual(user.skipped, 10)
        self.assertEqual(user.processed, 0)

    def test_valid_tagging(self):
        self.create_user_and_login("user")
        user = User.objects.get(username="user")
        self.assertEqual(user.skipped, 0)
        self.assertEqual(user.processed, 0)
        self.assertEqual(user.tags_count, 0)
        self.assertEqual(TaggingSpeed.objects.count(), 0)

        new_tags = ["foo", "bar"]

        self.client.post(url_for("fixtures.create_shreds"))

        res = self.client.get(url_for("next"))
        self.assert200(res)
        body = res.get_data(as_text=True)

        current_shred_id = self.parse_shred_id(body)
        current_shred = Cluster.objects.get(id=current_shred_id)
        self.assertEqual(current_shred.get_user_tags(user), None)

        res = self.client.post(
            url_for("next"), data={
                "_id": current_shred_id,
                "recognizable_chars": "foo\nbar\nfoo",
                "angle": 90,
                "tags": ["FOO", "foo", "Bar", "bAR"],
                "tagging_start": datetime.utcnow()
            })

        body = res.get_data(as_text=True)
        self.assert200(res)

        new_shred_id = self.parse_shred_id(body)
        current_shred.reload()
        user.reload()
        user_tag = current_shred.get_user_tags(user)

        self.assertNotEqual(new_shred_id, current_shred_id)

        self.assertEqual(user_tag.tags, new_tags)
        self.assertEqual(user_tag.angle, 90)
        self.assertEqual(user_tag.recognizable_chars, "foo\nbar\nfoo")

        self.assertEqual(current_shred.users_count, 1)
        self.assertEqual(current_shred.users_skipped, [])
        self.assertEqual(current_shred.users_processed[0].username,
                         user.username)

        self.assertEqual(user.skipped, 0)
        self.assertEqual(user.processed, 1)
        self.assertEqual(user.tags_count, 2)
        self.assertEqual(user.tags, new_tags)
        self.assertEqual(TaggingSpeed.objects.count(), 1)

        for tag_name in new_tags:
            tag = Tags.objects.get(title=tag_name)

            self.assertEqual(tag.is_base, False)
            self.assertEqual(tag.usages, 1)
            self.assertEqual(tag.shreds[0].id, current_shred_id)
            self.assertEqual(tag.created_by.username, user.username)
