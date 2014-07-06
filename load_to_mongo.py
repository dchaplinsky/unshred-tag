import sys
import os
import os.path
import json
from app import shreds, base_tags
import split
import fnmatch
from pymongo import ASCENDING
from boto.s3.connection import S3Connection
from boto.s3.key import Key

conn = S3Connection(os.environ.get("aws_access_key_id"),
                    os.environ.get("aws_secret_access_key"))
dst_bucket_name = 'kurchenko'
src_bucket_name = 'kurchenko_pink'

dst_bucket = conn.get_bucket(dst_bucket_name)
src_bucket = conn.get_bucket(src_bucket_name)


def upload_file(fname):
    k = Key(dst_bucket)
    k.key = fname
    k.set_contents_from_filename(fname)
    k.make_public()
    return "https://s3.amazonaws.com/%s/%s" % (dst_bucket_name, fname)

if __name__ == '__main__':
    dst_bucket.delete_keys(dst_bucket.get_all_keys())

    shreds.drop()
    flt = sys.argv[1]

    for src_key in src_bucket.get_all_keys():
        if not fnmatch.fnmatch(src_key.key, flt):
            continue

        fname = "/tmp/%s" % os.path.basename(src_key.key)
        src_key.get_contents_to_filename(fname)

        split.out_dir_name = os.path.splitext(os.path.basename(fname))[0]

        print("\n\nProcessing file %s from %s" % (fname, split.out_dir_name))
        orig_img, resulting_contours = split.process_file(fname)

        for c in resulting_contours:
            c["_id"] = "%s_%s" % (c["sheet"], c["name"])
            c["order"] = 0

            del(c["simplified_contour"])
            c["contour"] = c["contour"].tolist()

            imgs = "piece_fname", "features_fname", "piece_in_context_fname"

            for k in imgs:
                if k in c:
                    res = upload_file(c[k])
                    os.remove(c[k])
                    c[k] = res

            shreds.insert(c)

    shreds.ensure_index([("name", ASCENDING), ("sheet", ASCENDING)])
    shreds.ensure_index([("tags", ASCENDING)])

    base_tags.drop()

    with open("base_tags.json", "r") as f:
        tags = json.load(f)
        for tag in tags:
            base_tags.insert(tag)
