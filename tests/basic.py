import unittest
import app as unshred
from models.user import User


class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        unshred.app.config['TESTING'] = True
        unshred.app.config['MONGODB_SETTINGS']["DB"] = "unshred_test"
        cls.app = unshred.app.test_client()

    def test_login(self):
        usr = User(username="foo", password="bar", active=True)
        usr.save()

    def tearDown(self):
        pass
