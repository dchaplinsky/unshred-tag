import copy
import os

import pymongo
from mongoengine import connect, register_connection
from mongoengine.context_managers import switch_db

from models.shreds import Shred, Cluster, ClusterMember

# Does not overwrite data. Reads from 'clusters' collection, writes to 'cluster'
# and 'shred'.
SOURCE_DB_NAME = "unshred-staging"
TARGET_DB_NAME = SOURCE_DB_NAME


def transform_shred(shred_dict):
    shred = copy.deepcopy(shred_dict)

    shred_fields = {}
    cluster_fields = {}

    shred_fields_map = {
        'tags_suggestions': 'tags',
        'features_fname': 'mask_fname',
        'name': 'name',
        'sheet': 'sheet',
        'piece_fname': 'piece_fname',
        'piece_in_context_fname': 'piece_in_context_fname',
        'features': 'features',
        'contour': 'contour',
    }

    cluster_fields_map = {
        'batch': 'batch',
        'tags': 'tags',
        'usersSkipped': 'users_skipped',
        'usersProcessed': 'users_processed',
        'usersCount': 'users_count',
    }

    features_map = {
        'pos_width': 'width',
        'pos_height': 'height',
    }

    drop_fields = ['features_fname', 'summarizedTags']
    drop_features = ['pos_x', 'pos_y', 'angle', 'bottommost', 'topmost']

    for src, dst in shred_fields_map.items():
        shred_fields[dst] = shred.pop(src)

    for src, dst in cluster_fields_map.items():
        cluster_fields[dst] = shred.pop(src)

    for src, dst in features_map.items():
        shred_fields['features'][dst] = shred_fields['features'].pop(src)

    for name in drop_fields:
        if name in shred:
            del shred[name]
    for feature in drop_features:
        del shred_fields['features'][feature]

    shred_fields['contour'] = [c[0] for c in shred_fields['contour']]
    shred_fields['id'] = cluster_fields['id'] = shred.pop('_id')

    assert not shred, "Still has fields: %s" % shred.keys()
    return shred_fields, cluster_fields


def main():
    register_connection(alias="default", name=TARGET_DB_NAME)

    with switch_db(Shred, "default") as TargetShred, \
         switch_db(Cluster, "default") as TargetCluster:

        client = pymongo.MongoClient()
        source_db = client[SOURCE_DB_NAME]

        for src_shred in source_db.shreds.find({}):
            new_shred, cluster = transform_shred(src_shred)

            shred_obj = TargetShred.objects.create(**new_shred)
            cluster_member = ClusterMember(shred=shred_obj, position=[0, 0],
                                           angle=0)
            cluster['members'] = [cluster_member]
            cluster_obj = TargetCluster.objects.create(**cluster)

if __name__ == '__main__':
    main()
