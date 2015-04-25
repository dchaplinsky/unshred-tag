# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import (Flask, g, render_template, request, redirect,
                   url_for, session, abort)

from flask.ext.mongoengine import MongoEngine
from flask.ext import login

from users import init_social_login
from assets import init as assets_init
from models import Cluster, Pages, ShredTags, TaggingSpeed, Tags, User
from admin import admin_init
from utils import unique
import webapi

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
except ImportError:
    pass

# Disabled temporary because of
# https://github.com/mgood/flask-debugtoolbar/pull/66
# try:
#     from flask_debugtoolbar import DebugToolbarExtension
#     toolbar = DebugToolbarExtension(app)
# except ImportError:
#     pass

assets_init(app)
admin_init(app)

db = MongoEngine(app)

init_social_login(app, db)

if app.config["ENABLE_FIXTURES_ENDPOINTS"]:
    from fixtures import mod as fixtures_module
    app.register_blueprint(fixtures_module)


from metrics import mod as metrics_mod
app.register_blueprint(metrics_mod)

# TODO: docstrings everywhere!

# TODO: method of Tags QS
def get_tags():
    g.user.reload()  # To capture tags that has been just added

    base_tags = [t["title"] for t in Tags.objects.get_base_tags()]

    # using unique here to maintain order by popularity for base tags
    return filter(None, unique(base_tags + g.user.tags))


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template(
        "index.html",
        base_tags=Tags.objects.get_base_tags(order_by_category=True))


@app.route('/shred/<string:cluster_id>', methods=["GET", "POST"])
@login.login_required
def shred(cluster_id):
    cluster = Cluster.objects.get(id=cluster_id)
    if not cluster:
        abort(404)

    if request.method == "POST":
        # TODO: helper
        tags = set(map(unicode.lower, request.form.getlist("tags")))

        user_tags = cluster.get_user_tags(g.user)
        if not user_tags:
            abort(404)

        user_tags.tags = list(tags)
        user_tags.recognizable_chars = request.form.get(
            "recognizable_chars", "")
        user_tags.angle = int(request.form.get("angle", 0))
        cluster.save()

        User.objects(pk=g.user.id).update_one(
            add_to_set__tags=list(tags))

        for tag in tags:
            Tags.objects(pk=tag).update_one(
                set_on_insert__is_base=False,
                set_on_insert__created_by=g.user.id,
                set_on_insert__created_at=Tags().created_at,
                inc__usages=1,
                add_to_set__shreds=request.form["_id"],
                upsert=True)

        return render_template("_shred_snippet.html", cluster=cluster)
    else:
        return render_template(
            "_shred.html",
            cluster=cluster,
            auto_tags=cluster.auto_tags,
            all_tags=get_tags(),
            user_data=cluster.get_user_tags(g.user),
            edit=True,
        )


@app.route('/next', methods=["GET", "POST"])
@login.login_required
def next():
    if request.method == "POST":
        # TODO: helper
        tags = set(map(unicode.lower, request.form.getlist("tags")))

        Cluster.objects(pk=request.form["_id"]).update_one(
            push__tags=ShredTags(
                user=g.user.id,
                tags=list(tags),
                recognizable_chars=request.form.get("recognizable_chars", ""),
                angle=int(request.form.get("angle", 0))),
            inc__users_count=1,
            add_to_set__users_processed=g.user.id)

        User.objects(pk=g.user.id).update_one(
            inc__processed=1, inc__tags_count=len(tags),
            add_to_set__tags=list(tags))

        session["processed"] = session.get("processed", 0) + 1

        for tag in tags:
            Tags.objects(pk=tag).update_one(
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
            cluster=request.form["_id"],
            tags_count=len(tags),
            msec=(end - start).total_seconds() * 1000)

    cluster = Cluster.next_for_user(g.user, app.config['USERS_PER_SHRED'])

    auto_tags = cluster and cluster.auto_tags or []
    return render_template(
        "_shred.html",
        cluster=cluster,
        auto_tags=auto_tags,
        all_tags=get_tags(),
        tagging_start=datetime.utcnow(),

        # TODO: move to context processor
        processed_per_session=session.get("processed", 0),
        processed_total=User.objects(id=g.user.id).first()["processed"],
        rating=list(User.objects.order_by(
            "-processed").values_list("id")).index(g.user.id) + 1
    )


@app.route("/skip", methods=["POST"])
@login.login_required
def skip():
    Cluster.objects(pk=request.form["_id"]).update_one(
        add_to_set__users_skipped=g.user.id)
    User.objects(pk=g.user.id).update_one(inc__skipped=1)

    return redirect(url_for("next"))


@app.route("/review", methods=["GET"])
@login.login_required
def review():
    page = int(request.args.get('page', 1))

    items = (Cluster
             .objects(users_processed=g.user.id)
             .paginate(page=page, per_page=20))

    pages = Pages.objects(created_by=g.user.id)
    return render_template("review.html", items=items, pages=pages)


@app.route("/pages", methods=["GET", "POST"])
@login.login_required
def pages():
    if request.method == "POST":
        shreds = set(request.form.getlist("shreds"))
        page_name = request.form.get("page_name")
        page_id = request.form.get("page_id")

        if page_id:
            page = Pages.objects.get(pk=page_id)
        else:
            page, _ = Pages.objects.get_or_create(
                created_by=g.user.id, name=page_name)

        page.update(add_to_set__shreds=shreds)

        for shred in Cluster.objects(id__in=shreds):
            tags = shred.get_user_tags(g.user)
            if tags is not None:
                tags.pages = list(set(tags.pages + [page]))
            # TODO: else 404?

            shred.save()

    pages = Pages.objects(created_by=g.user.id)

    return render_template(
        "_pages.html",
        pages=pages)


@app.route("/stitch", methods=["GET"])
def stitch():
    return render_template("stitch.html")


app.register_blueprint(webapi.app, url_prefix='/api')


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
