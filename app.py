import os
import pymongo
from flask import Flask

app = Flask(__name__)

MONGODB_DB = "unshred"
MONGO_URL = os.environ.get('MONGOHQ_URL')
connection = pymongo.MongoClient(
    MONGO_URL if MONGO_URL else "mongodb://localhost/" + MONGODB_DB)

shreds = connection.get_default_database().shreds


@app.route('/')
def hello():
    return '<img src="%s">' % shreds.find_one()["piece_in_context_fname"]

if __name__ == "__main__":
    app.run(debug=True)
