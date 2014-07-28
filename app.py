from flask import Flask, render_template, request, redirect, url_for

from flask.ext.mongoengine import MongoEngine
from flask.ext import login

from users import init_social_login
from assets import init as assets_init
from models import Shreds, Tags

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
except ImportError:
    pass

db = MongoEngine(app)

init_social_login(app, db)

shreds = Shreds._get_collection()
base_tags = Tags._get_collection()


def get_next_shred():
    shred = shreds.find({str(g.user.id): None}).sort("usersCount").limit(1)[0]
    if shred:
        return shred
    return shreds.find({str(g.user.id): "skipped"})\
                        .sort("usersCount").limit(1)[0]


def get_tags():
    all_tags = set()
    for t in base_tags.find():
        all_tags.add(t["title"].lower())

    for t in shreds.distinct("tags"):
        if t is not None:
            all_tags.add(t.lower())

    return all_tags

def progress_per_user(id):
    return shreds.find({str(id): {"$exists": True, "$ne": "skipped"}}).count()

@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    print progress_per_user(g.user.id)
    return render_template("index.html",
                           base_tags=base_tags.find())


@app.route('/next', methods=["GET", "POST"])
def next():
    if request.method == "POST":
        shreds.update({"_id": request.form["_id"]},
                      {"$set": {str(g.user.id): map(unicode.lower,
                                            request.form.getlist("tags"))},
                       "$push": {"users": str(g.user.id)},
                       "$inc": {"usersCount": 1}
                       })

    return render_template("shred.html",
                           shred=get_next_shred(),
                           all_tags=get_tags()
                           )


@app.route("/skip", methods=["POST"])
def skip():
    shred = shreds.find_one({"_id": request.form["_id"]})

    shreds.update({"_id": request.form["_id"]},
                  {"$set": {str(g.user.id): "skipped"}})

    return redirect(url_for("next"))

if __name__ == "__main__":
    assets_init(app)
    app.run(debug=True)
