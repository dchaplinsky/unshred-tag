import os
import os.path
import json
import bson
import fnmatch
import urlparse
import shutil
import time
from glob import glob
from click import echo

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from unshred.split import SheetIO
from unshred.features import GeometryFeatures, ColourFeatures

from app import app
from models import Batches, Tags, Shreds


class AbstractStorage(object):
    def __init__(self, config):
        raise NotImplementedError

    def clear(self, dirname):
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

    def clear(self, dirname):
        keys = self.dst_bucket.list(dirname)
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

    def list(self, mask):
        return glob(os.path.join(self.src_dir, mask))

    def put_file(self, fname_src):
        return urlparse.urljoin(self.url, fname_src)

    def clear(self, dirname):
        shutil.rmtree(dirname, ignore_errors=True)

    def get_file(self, fname_src):
        return fname_src


def load_new_batch(flt, batch):
    if app.config["S3_ENABLED"]:
        strg = S3Storage(app.config)
    else:
        strg = LocalFSStorage(app.config)

    pages_processed = 0
    shreds_created = 0
    import_took = time.time()

    out_dir = os.path.join(app.config["SPLIT_OUT_DIR"], "batch_%s" % batch)
    strg.clear(out_dir)
    Shreds.objects(batch=batch).delete()

    for src_key in strg.list(flt):
        fname = strg.get_file(src_key)
        sheet_name = os.path.splitext(os.path.basename(fname))[0]

        echo("\n\nProcessing file %s from %s" % (fname, sheet_name))
        sheet = SheetIO(fname, sheet_name, [GeometryFeatures, ColourFeatures],
                        out_dir, "png")

        pages_processed += 1

        for c in sheet.get_shreds():
            c = c._asdict()
            c["id"] = "%s:%s_%s" % (batch, c["sheet"], c["name"])
            c["usersCount"] = 0
            c["batch"] = batch
            shreds_created += 1

            del(c["simplified_contour"])
            c["contour"] = c["contour"].tolist()

            imgs = "piece_fname", "features_fname", "piece_in_context_fname"

            for k in imgs:
                if k in c:
                    res = strg.put_file(c[k])
                    c[k] = res

            try:
                Shreds.objects.create(**c)
            except bson.errors.InvalidDocument:
                echo(c)
                raise

    Batches(
        _id=batch,
        name=batch,
        shreds_created=shreds_created,
        pages_processed=pages_processed,
        import_took=int((time.time() - import_took) * 1000)
    ).save()

    Shreds.ensure_index(["name", "sheet", "batch"])
    Shreds.ensure_index(["users_processed", "users_count", "batch"])
    Shreds.ensure_index(["users_skipped", "users_count", "batch"])


def import_tags(drop=False):
    if drop:
        Tags.objects(is_base=True).delete()

    added = 0
    updated = 0

    with open("fixtures/base_tags.json", "r") as f:
        tags = json.load(f)
        for tag in tags:
            _, created = Tags.objects.get_or_create(
                title=tag["title"], defaults=tag)
            if created:
                added += 1
            else:
                updated += 1

    Tags.ensure_index(["is_base", "usages", "category"])

    return added, updated


def list_batches():
    return Batches.objects.order_by("created")


def list_tags():
    return Tags.objects.order_by("-usages")
