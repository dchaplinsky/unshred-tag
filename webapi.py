import json
import uuid

from flask import Blueprint, jsonify, request

from models import Shred, Cluster, ClusterMember


app = Blueprint("webapi", __name__)


@app.route('/cluster', methods=["GET"])
@app.route('/cluster/<cluster_id>', methods=["GET"])
def get_cluster(cluster_id=None):
    """Renders a single cluster as json.

    If the cluster id is not provided, picks a random one.
    """
    batch = request.args.get("batch")
    if cluster_id is None:
        cluster = Cluster.get_some(batch=batch)
    else:
        cluster = Cluster.objects.get_or_404(pk=cluster_id)

    return jsonify({
        "success": True,
        "data": {
            "cluster": json.loads(cluster.to_json()),
        },
    })


@app.route('/shred/<shred_id>')
def get_shred(shred_id):
    """Looks up a single shred by id."""
    shred = Shred.objects.get_or_404(id=shred_id)
    return jsonify({'success': True,
                    'data': {
                        'shred': json.loads(shred.to_json())
                    }})


@app.route('/cluster', methods=['POST'])
def create_cluster():
    """Merges two clusters.

    Processes a POST request that should contain an object like:
    { "cluster": {
        "parents": ["parent1_id", "parent2_id"],
        "members": [{
            "shred": "shred1_id",
            "position": [100, 500],
            "angle": 35,
          },
          ...
        ]
    } }

    """

    req = request.get_json().get('cluster')

    parents = [Cluster.objects.get_or_404(pk=pk) for pk in req['parents']]

    if len(parents) != 2:
        response = jsonify({
            "success": False,
            "message": "Wrong number of good parents: %s" % req['parents']})
        response.status_code = 400
        return response

    if parents[0].batch != parents[1].batch:
        response = jsonify({
            "success": False,
            "message": "Parents are from different batches: %s %s" % (
                parents[0].batch, parents[1].batch)})
        response.status_code = 400
        return response

    member_fields = ['shred', 'position', 'angle']
    for member in req['members']:
        for field in member_fields:
            if field not in member:
                response = jsonify({
                    "success": False,
                    "message": "One of the members doesn't have all required "
                               "fields (%s): %s" % (member_fields, member),
                })
                response.status_code = 400
                return response

    cluster = Cluster(
            id=str(uuid.uuid1()),
            users_count=0,
            users_skipped=[],
            users_processed=[],
            batch=parents[0].batch,
            tags=[],
            parents=parents,
            members=[ClusterMember(
                shred=m['shred'], position=m['position'], angle=m['angle'])
                for m in req['members']],
    )
    cluster.save()

    return jsonify({
        "success": True,
        "id": cluster.id,
    })


@app.route('/cluster/many', methods=['POST'])
def get_clusters_many():
    """Looks up many clusters in batch.

    Should be called with a JSON request in POST body of form:
    { "ids": ["cluster1_id", ...,"clusterN_id"] }

    Returns:
        A JSON response like:
        { "success": True,
          "data": [Cluseter1(), ..., ClusterN()],
        }
        If the cluster for the requested id is missing, null is returned in
        corresponding position.
    """
    ids = list(request.get_json().get('ids'))

    json_mapping = {cluster.id: json.loads(cluster.to_json())
                    for cluster in Cluster.objects.filter(id__in=ids)}

    return jsonify({
        "success": True,
        "data": [json_mapping.get(c_id) for c_id in ids],
    })
