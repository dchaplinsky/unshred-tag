import json
import urllib

from flask import url_for

from models.shreds import Cluster
from . import BasicTestCase



class WebApiTest(BasicTestCase):
    def setUp(self):
        self.client.post(url_for("fixtures.reset_db"))
        self.client.post(url_for("fixtures.create_shreds"))

    def test_get_random_cluster(self):
        response = self.client.get(url_for('webapi.get_cluster'))
        self.assertTrue(response.json and response.json.get('success'))
        self.assertIn('cluster', response.json['data'])
        self.assertTrue(response.json['data']['cluster']['_id'])
        self.assertTrue(response.json['data']['cluster']['batch'])

    def test_get_cluster_by_id(self):
        cluster_id = "fixtures1:6_13"
        response = self.client.get(
            url_for('webapi.get_cluster',
                    cluster_id=cluster_id))
        self.assertTrue(response.json and response.json.get('success'))
        self.assertEqual(response.json['data']['cluster']['_id'],
                         cluster_id)
        self.assertTrue(response.json['data']['cluster']['members'])

    def test_get_cluster_by_bogus_id(self):
        cluster_id = "bogus cluster id"
        self.assert404(self.client.get(
            url_for('webapi.get_cluster',
                    cluster_id=cluster_id))
        )

    def test_get_shred(self):
        cluster_id = "fixtures1:6_13"
        response = self.client.get(
            url_for('webapi.get_cluster',
                    cluster_id=cluster_id))
        shred_id = response.json['data']['cluster']['members'][0]['shred']

        response = self.client.get(
            url_for('webapi.get_shred',
                    shred_id=shred_id))
        self.assertTrue(response.json and response.json['success'])

        for field in ['piece_fname', 'mask_fname', 'contour', 'features']:
            self.assertIn(field, response.json['data']['shred'])

        for feature in ['width', 'height', 'area']:
            self.assertIn(feature, response.json['data']['shred']['features'])

    def test_get_shred_bogus_id(self):
        shred_id = "bogus shred id"
        self.assert404(self.client.get(
            url_for('webapi.get_shred',
                    shred_id=shred_id))
        )

    def _get_mergeable_clusters(self):
        """Picks two clusters from the same batch.

        Returns:
            2-tuple of Cluster instances.
        """
        resp = self.client.get(
            url_for('webapi.get_cluster')).json['data']
        cluster1_id = resp['cluster']['_id']
        cluster1_batch = resp['cluster']['batch']
        cluster2_id = cluster1_id

        qs = urllib.urlencode({'batch': cluster1_batch})

        panic_counter = 0
        while cluster2_id == cluster1_id:
            # Sometimes it just won't give another cluster.
            if panic_counter > 100:
                return self._get_mergeable_clusters()
            resp = self.client.get(
                url_for('webapi.get_cluster') + "?" + qs)
            cluster2_id = resp.json['data']['cluster']['_id']
            panic_counter += 1

        cluster1 = Cluster.objects.get(pk=cluster1_id)
        cluster2 = Cluster.objects.get(pk=cluster1_id)

        return cluster1, cluster2

    def test_create_cluster(self):
        cluster1, cluster2 = self._get_mergeable_clusters()

        m1 = cluster1.members[0]
        m2 = cluster2.members[0]

        members = [{
                "shred": m1['shred'].id,
                "position": [10, 20],
                "angle": 15,
            }, {
                "shred": m2['shred'].id,
                "position": [30, 40],
                "angle": 25,
            },
        ]

        request = json.dumps({
            "cluster": {
                "parents": [cluster1.id, cluster2.id],
                "members": members,
            },
        })

        response = self.client.post(
            url_for('webapi.create_cluster'),
            content_type="application/json",
            data=request,
        )

        self.assertTrue(response.json)
        self.assertTrue(response.json['success'], response.json)
        new_cluster_id = response.json['id']

        cluster = Cluster.objects.get(pk=new_cluster_id)

        parent_ids = [p.id for p in cluster.parents]
        self.assertItemsEqual(parent_ids, [cluster1.id, cluster2.id])

        for want_member, got_member in zip(members, cluster.members):
            self.assertEqual(want_member['shred'], got_member.shred.id)
            self.assertEqual(want_member['position'], got_member.position)
            self.assertEqual(want_member['angle'], got_member.angle)

    def test_merge_one_cluster(self):
        cluster1, _ = self._get_mergeable_clusters()
        request = json.dumps({"cluster": {"parents": [cluster1.id]}})

        self.assert400(self.client.post(
            url_for('webapi.create_cluster'),
            content_type="application/json",
            data=request,
        ))

    def test_clusters_many(self):
        cluster_ids = ["fixtures1:6_13", "bogus id"]
        resp = self.client.post(
            url_for("webapi.get_clusters_many"),
            content_type="application/json",
            data=json.dumps({"ids": cluster_ids})
        )
        self.assertTrue(resp.json and resp.json['success'])
        self.assertEqual(len(resp.json['data']), len(cluster_ids))
        self.assertEqual(resp.json['data'][0]['_id'], cluster_ids[0])
        self.assertEqual(resp.json['data'][1], None)

