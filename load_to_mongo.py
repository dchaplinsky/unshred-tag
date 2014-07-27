import sys
import os
import os.path
import json
import bson
from app import shreds, base_tags, app
from unshred import Sheet
from unshred.features.base import GeometryFeatures
import fnmatch
from pymongo import ASCENDING
from boto.s3.connection import S3Connection
from boto.s3.key import Key


class AbstractStorage(object):
    def clear(self, config):
        raise NotImplementedError

    def get_file(self, fname_src):
        raise NotImplementedError

    def put_file(self, content, fname_src):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError


class S3Storage(AbstractStorage):
    def __init__(self, config):
        self.conn = S3Connection(config["S3_ACCESS_KEY_ID"],
                                 config["S3_SECRET_ACCESS_KEY"])

        self.dst_bucket_name = config["S3_DST_BUCKET_NAME"]

        self.src_bucket = self.conn.get_bucket(config["S3_SRC_BUCKET_NAME"])
        self.dst_bucket = self.conn.get_bucket(self.dst_bucket_name)

    def put_file(self, fname_src):
        k = Key(self.dst_bucket)
        k.key = fname_src
        k.set_contents_from_filename(fname_src)
        k.make_public()
        os.remove(fname_src)
        return "https://s3.amazonaws.com/%s/%s" % (self.dst_bucket_name,
                                                   fname_src)

    def clear(self):
        keys = self.dst_bucket.list()
        print(list(keys))
        self.dst_bucket.delete_keys(keys)

    def get_file(self, fname_src):
        fname = "/tmp/%s" % os.path.basename(fname_src.key)
        fname_src.get_contents_to_filename(fname)
        return fname

    def list(self, mask):
        return [k for k in self.src_bucket.list()
                if fnmatch.fnmatch(k.key, mask)]


class LocalFSStorage(AbstractStorage):
    def __init__(self, config):
        self.src_dir = config["LOCAL_FS_SRC_DIR"]
        self.url = config["LOCAL_FS_URL"]


if __name__ == '__main__':
    strg = S3Storage(app.config)
    strg.clear()

    shreds.drop()
    flt = sys.argv[1]

    for src_key in strg.list(flt):
        fname = strg.get_file(src_key)
        sheet_name = os.path.splitext(os.path.basename(fname))[0]

        print("\n\nProcessing file %s from %s" % (fname, sheet_name))
        sheet = Sheet(fname, sheet_name, [GeometryFeatures], "png")

        for c in sheet.resulting_contours:
            c["_id"] = "%s_%s" % (c["sheet"], c["name"])
            c["order"] = 0

            del(c["simplified_contour"])
            c["contour"] = c["contour"].tolist()

            imgs = "piece_fname", "features_fname", "piece_in_context_fname"

            for k in imgs:
                if k in c:
                    res = strg.put_file(c[k])
                    c[k] = res

            try:
                shreds.insert(c)
            except bson.errors.InvalidDocument:
                print(c)
                raise

    shreds.ensure_index([("name", ASCENDING), ("sheet", ASCENDING)])
    shreds.ensure_index([("tags", ASCENDING)])

    base_tags.drop()

    with open("base_tags.json", "r") as f:
        tags = json.load(f)
        for tag in tags:
            base_tags.insert(tag)
