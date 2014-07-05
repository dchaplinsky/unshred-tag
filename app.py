import os
import pymongo
from flask import Flask, render_template, request, redirect, url_for
from utils import requires_auth

app = Flask(__name__)

MONGODB_DB = "unshred"
MONGO_URL = os.environ.get('MONGOHQ_URL')
connection = pymongo.MongoClient(
    MONGO_URL if MONGO_URL else "mongodb://localhost/" + MONGODB_DB)

shreds = connection.get_default_database().shreds
base_tags = connection.get_default_database().tags


def get_next_shred():
    return shreds.find({"tags": None}).sort("order").limit(1)[0]


def get_tags():
    all_tags = set()
    for t in base_tags.find():
        all_tags.add(t["title"].lower())

    for t in shreds.distinct("tags"):
        if t is not None:
            all_tags.add(t.lower())

    return all_tags


@app.route('/')
@requires_auth
def index():
    return render_template("index.html",
                           base_tags=base_tags.find())


@app.route('/next', methods=["GET", "POST"])
@requires_auth
def next():
    if request.method == "POST":
        shreds.update({"_id": request.form["_id"]},
                      {"$set": {"tags": map(unicode.lower,
                                            request.form.getlist("tags"))}})

    return render_template("shred.html",
                           shred=get_next_shred(),
                           all_tags=get_tags()
                           )


@app.route("/skip", methods=["POST"])
def skip():
    shred = shreds.find_one({"_id": request.form["_id"]})

    shreds.update({"_id": request.form["_id"]},
                  {"$set": {"order": shred.get("order", 0) + 1}})

    return redirect(url_for("next"))

if __name__ == "__main__":
    app.run(debug=True)
