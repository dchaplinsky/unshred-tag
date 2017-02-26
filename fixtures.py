import os

from flask import (
    Blueprint,
    json
)

from flask_login import login_user as ext_login_user

from social_flask_mongoengine.models import FlaskStorage

from models import (Cluster, Tags, TaggingSpeed, User, Pages, Shred,
        ShredsDistances)
from utils import handle_exception_as_json

mod = Blueprint('fixtures', __name__, url_prefix='/fixtures')


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _import_from_file(fname, model):
    id_fieldname = model.id.name
    with open(os.path.join(FIXTURES_DIR, fname), "r") as f:
        objs = json.load(f)
        for obj in objs:
            if id_fieldname in obj:
                try:
                    model.objects(pk=obj[id_fieldname]).get()
                except model.DoesNotExist:
                    model.objects.create(**obj)
            else:
                model.objects.create(**obj)


@mod.route("/reset_db", methods=["POST"])
@handle_exception_as_json()
def reset_db():
    Tags.objects.delete()
    TaggingSpeed.objects.delete()
    Cluster.objects.delete()
    Shred.objects.delete()
    ShredsDistances.objects.delete()
    User.objects.delete()
    Pages.objects.delete()
    FlaskStorage.user.objects.delete()
    FlaskStorage.nonce.objects.delete()
    FlaskStorage.association.objects.delete()
    FlaskStorage.code.objects.delete()


@mod.route("/create_users", methods=["POST"])
@handle_exception_as_json()
def create_users():
    _import_from_file("users.json", User)


@mod.route("/create_base_tags", methods=["POST"])
@handle_exception_as_json()
def create_base_tags():
    _import_from_file("base_tags.json", Tags)


@mod.route("/create_shreds", methods=["POST"])
@handle_exception_as_json()
def create_shreds():
    _import_from_file("shreds.json", Shred)
    _import_from_file("clusters.json", Cluster)


@mod.route("/login_user/<string:username>", methods=["POST"])
@handle_exception_as_json()
def login_user(username):
    usr = User.objects.get(username=username)
    ext_login_user(usr)
