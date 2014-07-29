from flask import Flask, g, render_template, request, redirect, url_for

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
    # UC 1: (Not User) and (usersCount < 3)
    try:
        return shreds.find({"tags.user": {"$ne": str(g.user.id)}, \
            "$or": [{"usersCount": {"$exists": False}}, \
                    {"usersCount": {"$lt": app.config["USERS_PER_SHRED"] + 1}}
                    ]}).sort("usersCount").limit(1)[0]
    except IndexError, e:
        pass

    # UC 2: (User) and (tags.tags == skipped)
    # in this case we should delete record marked as 'skipped'
    try:
        shred = shreds.find({"tags.user": str(g.user.id), \
            "tags.tags": "skipped"}).sort("usersCount").limit(1)[0]
        shreds.update({"_id": shred["_id"]}, {"$pull": {'tags': \
            {"user": str(g.user.id), "tags": "skipped"}}})
        return shred
    except IndexError, e:
        pass

    # UC 3: (Not User)
    return shreds.find({"tags.user": {"$ne": str(g.user.id)}})\
        .sort("usersCount").limit(1)[0]


def get_tags():
    all_tags = set()
    for t in base_tags.find():
        all_tags.add(t["title"].lower())

    for t in shreds.distinct("tags.tags"):
        if t is not None:
            all_tags.add(t.lower())

    return all_tags


def progress_per_user(id):
    return shreds.find({"tags.user": str(id), "tags.tags": \
        {"$exists": True, "$ne": "skipped"}}).count()


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template("index.html",
                           base_tags=base_tags.find())


@app.route('/next', methods=["GET", "POST"])
def next():
    if request.method == "POST":
        shreds.update({"_id": request.form["_id"]},
                      {"$push": {"tags": {"user": str(g.user.id),
                       "tags": map(unicode.lower, request.form.getlist("tags"))}},
                       "$inc": {"usersCount": 1},
                       "$addToSet": {"summarizedTags": {"$each": \
                                map(unicode.lower, request.form.getlist("tags"))}}
                       })

    return render_template("shred.html",
                           shred=get_next_shred(),
                           all_tags=get_tags()
                           )


@app.route("/skip", methods=["POST"])
def skip():
    shred = shreds.find_one({"_id": request.form["_id"]})

    shreds.update({"_id": request.form["_id"]},
                  {"$push": {"tags":
                    {"user": str(g.user.id), "tags": "skipped"}}})

    return redirect(url_for("next"))

if __name__ == "__main__":
    assets_init(app)
    app.run(debug=True)
