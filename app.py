# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, g, render_template, request, redirect, \
    url_for, session

from flask.ext.mongoengine import MongoEngine
from flask.ext import login

from users import init_social_login
from assets import init as assets_init
from models import Shreds, Tags, TaggingSpeed, User, ShredTags
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


def get_next_shred():
    shred = Shreds\
        .objects(users_processed__ne=g.user.id, users_skipped__ne=g.user.id,
                 users_count__lte=app.config["USERS_PER_SHRED"])\
        .order_by("batch", "users_count").first()

    if shred:
        return shred

    shred = Shreds\
        .objects(users_skipped=g.user.id,
                 users_count__lte=app.config["USERS_PER_SHRED"])\
        .order_by("batch", "users_count").first()

    if shred:
        shred.update_one(pull__users_skipped=g.user.id)

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
            for suggestion in shred.tags_suggestions]

    return filter(None, set(auto))


def progress_per_user(user_id):
    return Shreds\
        .objects(
            tags__user=user_id, tags__tags__exists=True,
            tags__tags__ne="skipped")\
        .count()


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
        Shreds.objects(pk=request.form["_id"]).update_one(
            push__tags=ShredTags(user=g.user.id, tags=list(tags)),
            inc__users_count=1,
            add_to_set__summarized_tags=list(tags),
            add_to_set__users_processed=g.user.id)

        User.objects(pk=g.user.id).update_one(
            inc__processed=1, inc__tags_count=len(tags),
            add_to_set__tags=list(tags))

        session["processed"] = session.get("processed", 0) + 1

        for tag in tags:
            Tags.objects(pk=tag.capitalize()).update_one(
                set_on_insert__is_base=False,
                set_on_insert__created_by=g.user.id,
                set_on_insert__created_at=Tags().created_at,
                inc__usages=1,
                add_to_set__shreds=request.form["_id"],
                upsert=True)

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
                           tagging_start=datetime.utcnow(),
                           processed_per_session=session.get("processed", 0),
                           processed_total=User.objects(id=g.user.id)\
                                .first()["processed"],
                           rating=list(User.objects.order_by("-processed")\
                                .values_list("id")).index(g.user.id) + 1
                           )


@app.route("/skip", methods=["POST"])
def skip():
    Shreds.objects(pk=request.form["_id"]).update_one(
        add_to_set__users_skipped=g.user.id)
    User.objects(pk=g.user.id).update_one(inc__skipped=1)

    return redirect(url_for("next"))


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
