from flask import Flask, g, render_template, request, redirect, url_for
from flask.ext.mongoengine import MongoEngine
from flask.ext import login

from social.apps.flask_me_app.routes import social_auth
from social.apps.flask_me_app.models import init_social
from social.apps.flask_me_app.template_filters import backends

from assets import init as assets_init

from models.user import User

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
except ImportError:
    pass


db = MongoEngine(app)
mongo = db.connection

app.register_blueprint(social_auth)
init_social(app, db)

login_manager = login.LoginManager()
login_manager.login_view = 'main'
login_manager.login_message = ''
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    try:
        return User.objects.get(id=userid)
    except (TypeError, ValueError):
        pass


@app.before_request
def global_user():
    g.user = login.current_user


@app.context_processor
def inject_user():
    try:
        return {'user': g.user}
    except AttributeError:
        return {'user': None}


app.context_processor(backends)

def get_next_shred():
    return mongo.db.shreds.find({"tags": None}).sort("order").limit(1)[0]


def get_tags():
    all_tags = set()
    for t in mongo.db.tags.find():
        all_tags.add(t["title"].lower())

    for t in mongo.db.shreds.distinct("tags"):
        if t is not None:
            all_tags.add(t.lower())

    return all_tags


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template("index.html",
                           base_tags=mongo.db.tags.find())


@app.route('/next', methods=["GET", "POST"])
def next():
    if request.method == "POST":
        mongo.db.shreds.update({"_id": request.form["_id"]},
                      {"$set": {"tags": map(unicode.lower,
                                            request.form.getlist("tags"))}})

    return render_template("shred.html",
                           shred=get_next_shred(),
                           all_tags=get_tags()
                           )


@app.route("/skip", methods=["POST"])
def skip():
    shred = mongo.db.shreds.find_one({"_id": request.form["_id"]})

    mongo.db.shreds.update({"_id": request.form["_id"]},
                  {"$set": {"order": shred.get("order", 0) + 1}})

    return redirect(url_for("next"))

if __name__ == "__main__":
    assets_init(app)
    app.run(debug=True)
