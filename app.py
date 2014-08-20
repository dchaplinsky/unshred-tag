# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, g, render_template, request, redirect, url_for

from flask.ext.mongoengine import MongoEngine
from flask.ext import login

from users import init_social_login
from assets import init as assets_init
from models import Shreds, Tags, TaggingSpeed, User
from admin import admin_init

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
except ImportError:
    pass

assets_init(app)
admin_init(app)

db = MongoEngine(app)

init_social_login(app, db)

shreds = Shreds._get_collection()
users = User._get_collection()


def get_next_shred():
    shred = shreds.find_one(
        {"$query": {"usersProcessed": {"$ne": str(g.user.id)},
                    "usersSkipped": {"$ne": str(g.user.id)},
                    "usersCount": {"$lte": app.config["USERS_PER_SHRED"]}
                    }}, sort=[("batch", 1),
                              ("usersCount", 1)])

    if shred:
        return shred

    shred = shreds.find_one(
        {"$query": {"usersSkipped": str(g.user.id),
                    "usersCount": {"$lte": app.config["USERS_PER_SHRED"]}
                    }}, sort=[("batch", 1),
                              ("usersCount", 1)])

    if shred:
        shreds.update({"_id": shred["_id"]},
                      {"$pull": {'usersSkipped': str(g.user.id)}})

    return shred


def get_tags():
    return [unicode(t["title"]).lower()
            for t in Tags.objects.order_by("-usages")]


def get_tag_synonyms():
    mapping = {}
    for t in Tags.objects(synonyms__exists=True):
        for s in t["synonyms"]:
            mapping[s] = t["title"]

    return mapping


def get_auto_tags(shred):
    mapping = get_tag_synonyms()
    auto = [mapping.get(suggestion)
            for suggestion in shred.get("tags_suggestions", [])]

    return filter(None, set(auto))


def progress_per_user(id):
    return shreds.find(
        {"tags.user": str(id),
         "tags.tags": {"$exists": True, "$ne": "skipped"}}).count()


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template("index.html",
                           base_tags=Tags.objects.all())


@app.route('/next', methods=["GET", "POST"])
def next():
    if request.method == "POST":
        tags = set(map(unicode.lower, request.form.getlist("tags")))
        shreds.update({"_id": request.form["_id"]},
                      {"$push": {"tags": {"user": str(g.user.id),
                       "tags": list(tags)}},
                       "$inc": {"usersCount": 1},
                       "$addToSet": {"summarizedTags": {"$each": list(tags)},
                                     "usersProcessed": str(g.user.id)}
                       })

        users.update({"_id": g.user.id},
                     {"$inc": {"processed": 1, "tagsCount": len(tags)},
                      "$addToSet": {"tags": {"$each": list(tags)}}})

        for tag in tags:
            db_tag, _ = Tags.objects.get_or_create(
                title=tag.capitalize(),
                defaults={
                    "is_base": False,
                    "created_by": g.user.id
                }
            )
            db_tag.update(inc__usages=1,
                          add_to_set__shreds=request.form["_id"])

        start = datetime.strptime(request.form["tagging_start"],
                                  '%Y-%m-%d %H:%M:%S.%f')
        end = datetime.utcnow()
        TaggingSpeed.objects.create(
            user=g.user.id,
            shred=request.form["_id"],
            tags_count=len(tags),
            msec=(end - start).total_seconds() * 1000)

    shred = get_next_shred()
    return render_template("shred.html",
                           shred=shred,
                           auto_tags=get_auto_tags(shred),
                           all_tags=get_tags(),
                           tagging_start=datetime.utcnow()
                           )


@app.route("/skip", methods=["POST"])
def skip():
    shreds.update({"_id": request.form["_id"]},
                  {"$addToSet": {"usersSkipped": str(g.user.id)}})

    users.update({"_id": g.user.id}, {"$inc": {"skipped": 1}})

    return redirect(url_for("next"))

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
