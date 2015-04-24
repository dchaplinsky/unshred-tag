/*global $ Matrix Point */
/**
 * Represents an instance of UnshredTag API client.
 * @constructor
 * @param {string} baseUrl - Base URL to use for HTTP requests, e.g. "/api".
 */
var UnshredAPIClient = function (baseUrl) {
    this.baseUrl = baseUrl;

    // Attributes handle shred cache;
    // shredCache is a mapping of shredId -> shredObj;
    this.shredCache = {};
    // shredCallbacksPending maps shredId -> [success(), error()] callbacks 
    // whileshred request is in-flight.
    this.shredCallbacksPending = {};
    // Maximum number of shred cache entries.
    this.shredCacheSize = 100;
};


/**
 * Constructs and sends an HTTP request to an API endpoint.
 *
 * @param {string} type - HTTP request type.
 * @param {path} path - Path under baseUrl for request (no leading "/").
 * @param success - A success callback, called with returned data as arg.
 * @param error - Failure callback. Called on error.
 * @data {Object} [data] - Optional data object to serialize as json and send
 *      with request.
 */
UnshredAPIClient.prototype.Request = function(type, path, success, error, data) {
    var opts = {
        type: type,
        url: this.baseUrl + "/" + path,
        dataType: 'json',
        contentType: 'application/json',
        success: success,
        error: error
    };
    if (data) {
        opts.data = JSON.stringify(data);
    }
    $.ajax(opts);
};

/**
 * Fetches a single Shred instance.
 *
 * @param {string} shredId - Shred ID to fetch.
 * @param success - Success callback. Called with shred instance as an argument.
 * @param error - Failure callback.
 */
UnshredAPIClient.prototype.GetShred = function (shredId, success, error) {
    console.log("Getting shred " + shredId);
    if (this.shredCache[shredId] !== undefined) {
        success(this.shredCache[shredId]);
        return;
    }
    if (this.shredCallbacksPending[shredId] !== undefined) {
        this.shredCallbacksPending[shredId].push([success, error]);
        return;
    }
    if (Object.keys(this.shredCache).length >= this.shredCacheSize) {
        this.shredCache = {};
    }
    this.shredCallbacksPending[shredId] = [[success, error]];

    var client = this;
    this.Request("GET", "shred/" + shredId, function (response_data) {
        client.shredCache[shredId] = response_data.data.shred;
        var callbacks;
        while ((callbacks = client.shredCallbacksPending[shredId].pop())
                !== undefined) {
            callbacks[0](response_data.data.shred);
        }
        delete client.shredCallbacksPending[shredId];
    }, function(error) {
        var callbacks;
        while ((callbacks = client.shredCallbacksPending[shredId].pop())
                !== undefined) {
            callbacks[1](error);
        }
        delete client.shredCallbacksPending[shredId];
    });
};

/**
 * Fetches a single Cluster instance.
 *
 * @param {string} clusterId - Shred ID to fetch.
 * @param success - Success callback. Called with Cluster instance as an
 *      argument.
 * @param error - Failure callback.
 */
UnshredAPIClient.prototype.GetCluster = function (clusterId, success, error) {
    console.log("Getting cluster " + clusterId);
    var path = "cluster";
    if (clusterId !== null) {
        path += "/" + clusterId;
    }
    this.Request("GET", path, function (response_data) {
        success(response_data.data.cluster);
    }, error);
};

/**
 * Fetches a pair of clusters from the backend. The pair is expected to be
 * somewhat related, possibly suitable for stitching.
 *
 * TODO: Switch to the actual corresponding backend method, when it's
 * implemented.
 *
 * @param success - Success callback. On success called with two cluster
 *      objects.
 * @param error - Failure callback.
 */
UnshredAPIClient.prototype.GetClusterPairForStitching = function(success, error) {
    console.log("Getting cluster pair.");
    var pair = [];

    var receiveCluster = function(clusterObj) {
        pair.push(clusterObj);
        if (pair.length === 2) {
            success(pair[0], pair[1]);
        }
    };

    for (var i = 0; i < 2; i++) {
        this.GetCluster(null, receiveCluster, error);
    }
};

/**
 * Merges two clusters, given their relative positions.
 *
 * @param cluster1 - An object with 'members' and '_id' fields. Every member has
 *      'shred', 'position', 'angle' fields.
 * @param position1 - Relative position of cluster1. List of [x, y].
 * @param angle1 - Relative angle of cluster1 in degrees.
 * @param cluster2 - Second cluster object. Same type as cluster1.
 * @param position2 - Relative position of cluster2. List of [x, y].
 * @param angle2 - Relative angle of cluster2 in degrees.
 * @param success - Success callback. On success called with a single argument -
 *      string new cluster id.
 * @param error - Failure callback.
 */
UnshredAPIClient.prototype.MergeClusters = function (cluster1, position1,
                                                     angle1, cluster2,
                                                     position2, angle2,
                                                     success, error) {
    // Angle in degrees.
    //
    // Translate to cluster1's [0, 0] as origin.
    position2[0] -= position1[0];
    position1[0] -= position1[0];
    position2[1] -= position1[1];
    position1[1] -= position1[1];

    var degreesToRadians = function(angle) { return angle * Math.PI / 180; };
    var radiansToDegrees = function(angle) { return angle / (Math.PI / 180); };
    var copyMember = function(member) { return { shred: member.shred, position: member.position, angle: member.angle }; };

    // Angle is in degrees. Need radians for rotation matrix.
    angle1 = degreesToRadians(angle1);
    angle2 = degreesToRadians(angle2);

    var members = [];

    // Transform cluster1's members.
    for (var i = 0; i < cluster1.members.length; i++) {
        members.push(copyMember(cluster1.members[i]));
    }

    // m1 rotates clusters' origins around (0,0);
    var m1 = Matrix().rotate(-angle1);
    // m2 rotates shred origins around cluster2 origin.
    var m2 = Matrix().rotate(angle2);

    var cluster2Position = Point(position2[0], position2[1]);
    for (var j = 0; j < cluster2.members.length; j++) {
        var member = copyMember(cluster2.members[j]);
        var p = Point(member.position[0], member.position[1]);

        // Rotate member base point around it's cluster's origin.
        p = m2.transformPoint(p);

        // Transform to coordinates relative to base cluster's origin.
        p = p.add(cluster2Position);
        // Rotate member origin around base cluster's origin.
        p = m1.transformPoint(p);

        member.position = [p.x, p.y];
        // Angle to degrees.
        member.angle = member.angle + radiansToDegrees(angle2-angle1);

        members.push(member);
    }

    var data = {
        cluster: {
            parents: [cluster1._id, cluster2._id],
            members: members
        }
    };

    console.log(data);
    this.Request("POST", "cluster", function (response_data) {
        success(response_data.id);
    }, error, data);
    return data;
};
