from flask import (
    Blueprint,
    json
)

from flask.ext.login import login_user as ext_login_user

from social.apps.flask_me_app.models import FlaskStorage

from models import (Cluster, Tags, TaggingSpeed, User, Pages, Shred,
        ShredsDistances)
from utils import handle_exception_as_json

mod = Blueprint('fixtures', __name__, url_prefix='/fixtures')


def _import_from_file(fname, model):
    id_fieldname = model.id.name
    with open(fname, "r") as f:
        objs = json.load(f)
        for obj in objs:
            if id_fieldname in obj:
                model.objects.get_or_create(pk=obj[id_fieldname], defaults=obj)
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
    _import_from_file("fixtures/users.json", User)


@mod.route("/create_base_tags", methods=["POST"])
@handle_exception_as_json()
def create_base_tags():
    _import_from_file("fixtures/base_tags.json", Tags)


@mod.route("/create_shreds", methods=["POST"])
@handle_exception_as_json()
def create_shreds():
    _import_from_file("fixtures/shreds.json", Shred)
    _import_from_file("fixtures/clusters.json", Cluster)


@mod.route("/login_user/<string:username>", methods=["POST"])
@handle_exception_as_json()
def login_user(username):
    usr = User.objects.get(username=username)
    ext_login_user(usr)
