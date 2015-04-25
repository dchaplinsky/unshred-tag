import os
import os.path
import json
import bson
import fnmatch
import urlparse
import shutil
from glob import glob
from click import echo

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from unshred.split import SheetIO
from unshred.features import GeometryFeatures, ColourFeatures

from app import app
from models import Cluster, ClusterMember, Shred, Tags


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


def load_new_batch(fname_glob, batch):
    if app.config["S3_ENABLED"]:
        storage = S3Storage(app.config)
    else:
        storage = LocalFSStorage(app.config)

    pages_processed = 0
    shreds_created = 0

    out_dir = os.path.join(app.config["SPLIT_OUT_DIR"], "batch_%s" % batch)
    storage.clear(out_dir)
    Cluster.objects(batch=batch).delete()

    for src_key in storage.list(fname_glob):
        fname = storage.get_file(src_key)
        sheet_name = os.path.splitext(os.path.basename(fname))[0]

        echo("\n\nProcessing file %s from %s" % (fname, sheet_name))
        sheet = SheetIO(fname, sheet_name, [GeometryFeatures, ColourFeatures],
                        out_dir, "png")

        image_path_fields = ["piece_fname", "mask_fname",
                             "piece_in_context_fname"]

        # TODO: Remove when all field names match unshred's.
        field_name_map = {
            # Unshred-tag name: unshred name.
            "mask_fname": "features_fname",
        }
        drop_fields = ['simplified_contour', 'img_roi']
        drop_features = ['on_sheet_height', 'on_sheet_width', 'on_sheet_angle',
                'bottommost', 'topmost', 'on_sheet_x', 'on_sheet_y']


        pages_processed += 1

        for shred in sheet.get_shreds():
            shred = shred._asdict()
            shred["id"] = "%s:%s_%s" % (batch, shred["sheet"], shred["name"])
            shreds_created += 1

            def _convert_opencv_contour(contour):
                """Converts opencv contour to a list of pairs."""
                return contour.reshape((len(contour), 2)).tolist()
            shred["contour"] = _convert_opencv_contour(
                shred["simplified_contour"])
            shred['tags'] = shred.pop('tags_suggestions')

            for field in drop_fields:
                del shred[field]
            for field in drop_features:
                del shred['features'][field]

            cluster = {}
            cluster["id"] = shred["id"]
            cluster["users_count"] = 0
            cluster["batch"] = batch

            for model_field_name in image_path_fields:
                import_field_name = field_name_map.get(model_field_name,
                                                       model_field_name)
                image_path = shred.pop(import_field_name)
                res = storage.put_file(image_path)
                shred[model_field_name] = res

            cluster["parents"] = []
            try:
                shred_obj = Shred.objects.create(**shred)
                cluster_member = ClusterMember(shred=shred_obj, position=[0, 0],
                                               angle=0)
                cluster["members"] = [cluster_member]
                Cluster.objects.create(**cluster)
            except bson.errors.InvalidDocument:
                echo(shred)
                raise

    Cluster.ensure_index(["users_processed", "users_count", "batch"])
    Cluster.ensure_index(["users_skipped", "users_count", "batch"])


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
    batch_counts = Cluster._get_collection().aggregate([
        {
            '$group': {
                '_id': '$batch',
                'shreds_created': {
                    '$sum': 1}
                }
        },
        {
            '$sort': {
                'name': 1,
            },
        }])['result']
    return [{'name': item['_id'], 'shreds_created': item['shreds_created']}
            for item in batch_counts]



def list_tags():
    return Tags.objects.order_by("-usages")
