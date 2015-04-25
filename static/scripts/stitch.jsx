/** The file describes shred stitching UI.
 *
 * The UI is a hierarchy of React.js components. Every component refreshes
 * on its state updates (internal) and props updates (coming from
 * parent). The components hierarchy:
 *   StitchingUI
 *     BaseClusterTool
 *     Sandbox
 *       Cluster (base)
 *       Cluster (candidate)
 *       SaveBtn
 *     CandidatesTools
 *       Candidate
 *         Cluster (candidates with base, side by side)
 *
 *   Cluster
 *     ClusterMember (every shred's image)
 *
 */
/*global React $ UnshredAPIClient */

var ClusterMember = React.createClass({
    propTypes: {
        member: React.PropTypes.shape({
            shred: React.PropTypes.string.isRequired,
            angle: React.PropTypes.number.isRequired,
            position: React.PropTypes.arrayOf(React.PropTypes.number).isRequired
        }),
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired
    },
    getInitialState: function() {
        return {
            shredObj: null
        };
    },
    componentWillMount: function() {
        this._fetchShred(this.props.member.shred);
    },
    componentWillReceiveProps: function(nextProps) {
        this._fetchShred(nextProps.member.shred);
    },
    componentDidMount: function() { this.componentDidUpdate(); },
    componentDidUpdate: function() {
        var img = $(React.findDOMNode(this));

        var member = this.props.member;
        var component = this;

        img.load(function() {
            img.freetrans({
                x: member.position[0],
                y: member.position[1],
                angle: member.angle,
                "rot-origin": "0 0"
            }).freetrans('destroy');
        });
    },
    _fetchShred: function(shredId) {
        if (this.state.shredObj && (this.state.shredObj._id !== shredId)) {
            return;
        }
        var component = this;
        this.props.client.GetShred(shredId, function(shredObj) {
            component.setState({shredObj: shredObj});
        }, function(error) {console.log(error); });
    },
    render: function() {
        if (!this.state.shredObj) { return null; }

        var shred = this.state.shredObj;
        return (
            <img className="stitch-shred"
                src={shred.piece_fname} />
        );
    }
});

var Cluster = React.createClass({
    propTypes: {
        clusterObj: React.PropTypes.shape({
            members: React.PropTypes.array.isRequired
        }),
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired,
        className: React.PropTypes.string,
        offsetLeft: React.PropTypes.number,
        freetrans: React.PropTypes.bool
    },
    getDefaultProps: function() {
        return {
            className: "",
            offsetLeft: 0,
            freetrans: true
        };
    },
    componentDidMount: function() { this.componentDidUpdate(); },
    componentDidUpdate: function() {
        var container = $(React.findDOMNode(this));
        container.css('left', this.props.offsetLeft);
        // Not required for candidates.
        if (this.props.freetrans){
            container.freetrans({
                "rot-origin": "0% 0%",
                x: this.props.offsetLeft,
                y: 0,
                angle: 0
            });
        }
    },
    getTransformOptions: function() {
        if (!this.props.freetrans) {
            return null;
        }
        var options = $(React.findDOMNode(this)).freetrans('getOptions');
        return {
            position: {
                x: options.x,
                y: options.y
            },
            angle: options.angle
        };
    },
    render: function() {
        var component = this;
        var members = this.props.clusterObj.members.map(
            function(member, i) {
                return (
                    <ClusterMember
                        client={component.props.client}
                        member={member}
                        key={member.shred}
                    />
                );
            }
        );
        var className = "cluster " + this.props.className;

        return (
            <div className={className}>
                {members}
            </div>
        );
    }
});

var Sandbox = React.createClass({
    propTypes: {
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired,
        clusterObj1: React.PropTypes.shape({
            members: React.PropTypes.array.isRequired
        }),
        clusterObj2: React.PropTypes.shape({
            members: React.PropTypes.array.isRequired
        })
    },
    getDefaultProps: function() {
        return {
            clusterObj1: null,
            clusterObj2: null
        };
    },
    /** If the clusters are set returns list of their React components. null otherwise */
    getClusters: function() {
        if (this.props.clusterObj1 !== null && this.props.clusterObj2 !== null) {
            return [this.refs.baseCluster, this.refs.candidateCluster];
        } else {
            return null;
        }
    },
    render: function() {
        var cluster1, cluster2;
        if (this.props.clusterObj1 !== null && this.props.clusterObj2 !== null) {
            cluster1 = (
                <Cluster clusterObj={this.props.clusterObj1}
                    className="cluster-base"
                    client={this.props.client}
                    ref="baseCluster"
                    offsetLeft={-100} />
            );
            cluster2 = (
                <Cluster clusterObj={this.props.clusterObj2}
                    className="cluster-candidate"
                    client={this.props.client}
                    ref="candidateCluster"
                    offsetLeft={100} />
            );
        }
        return (
            <div className="stitch-middle">
                <div className='stitch-sandbox'>
                    {cluster1}
                    {cluster2}
                </div>
                <SaveBtn client={this.props.client}
                         getClusters={this.getClusters}
                         />
            </div>
        );
    }
});

var SaveBtn = React.createClass({
    propTypes: {
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired,
        getClusters: React.PropTypes.func.isRequired
    },
    _storeState: function() {
        var clusters = this.props.getClusters();
        if (clusters === null) {
            return;
        }
        var baseClusterComponent = clusters[0];
        var candidateClusterComponent = clusters[1];

        var baseCluster = baseClusterComponent.props.clusterObj;
        var candidateCluster = candidateClusterComponent.props.clusterObj;

        var baseClusterState = baseClusterComponent.getTransformOptions();
        var candidateClusterState = candidateClusterComponent.getTransformOptions();

        var data = this.props.client.MergeClusters(
            baseCluster, baseClusterState.position, baseClusterState.angle,
            candidateCluster, candidateClusterState.position, candidateClusterState.angle,
            this._clusterCreated, function(err) { console.log(err); });
    },
    _clusterCreated: function(clusterId) {
        this.props.client.GetCluster(clusterId, function(clusterObj) {
            console.log(clusterObj);
        }, function(error) { console.log(error); });
        console.log("New cluster id: ", clusterId);
    },
    render: function() {
        return (
            <button
                className='save-cluster btn btn-success'
                onClick={this._storeState}>
                Save
            </button>
        );
    }
});

var Candidate = React.createClass({
    propTypes: {
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired,
        clusterObj1: React.PropTypes.shape({
            members: React.PropTypes.array.isRequired
        }),
        clusterObj2: React.PropTypes.shape({
            members: React.PropTypes.array.isRequired
        }),
        setState: React.PropTypes.func.isRequired
    },
    componentWillReceiveProps: function(nextProps) {
        var candidateDiv = React.findDOMNode(this);
        $(candidateDiv).removeClass("selected");
    },
    _candidateSelected: function() {
        this.props.setState({
            clusterObj1: this.props.clusterObj1,
            clusterObj2: this.props.clusterObj2
        });

        var candidateDiv = React.findDOMNode(this);
        $('.candidate').removeClass("selected");
        $(candidateDiv).addClass("selected");
    },
    render: function() {
        return (
            <div className="candidate" onClick={this._candidateSelected}>
                <Cluster clusterObj={this.props.clusterObj1}
                    client={this.props.client}
                    freetrans={false}
                    offsetLeft={0} />
                <Cluster clusterObj={this.props.clusterObj2}
                    client={this.props.client}
                    freetrans={false}
                    offsetLeft={200} />
            </div>
        );
    }
});

var CandidatesTools = React.createClass({
    numberCandidates: 9,
    propTypes: {
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired,
        setState: React.PropTypes.func.isRequired
    },
    getInitialState: function() {
        return {
            candidates: []
        };
    },
    componentWillMount: function() {
        this._populateCandidates();
    },
    _populateCandidates: function() {
        var newCandidatePairs = [];
        var component = this;

        var storeCandidatePair = function(clusterObj1, clusterObj2) {
            newCandidatePairs.push([clusterObj1, clusterObj2]);
            if (newCandidatePairs.length === component.numberCandidates) {
                component.setState({
                    candidates: newCandidatePairs
                });
            }
        };
        for (var i = 0; i < this.numberCandidates; i++) {
            this.props.client.GetClusterPairForStitching(storeCandidatePair,
                function(error) {
                    console.log("Error getting candidate cluster: "+error);
                });
        }
    },
    render: function() {
        var component = this;
        var candidates = this.state.candidates.map(function(candidate) {
            return (
                <Candidate
                    clusterObj1={candidate[0]}
                    clusterObj2={candidate[1]}
                    client={component.props.client}
                    setState={component.props.setState}
                    key={candidate[0]._id + candidate[1]._id} />
            );
        });
        return (
            <div className='candidates-panel'>
                <button
                    className="more-candidates btn btn-primary"
                    onClick={this._populateCandidates}>
                    Get more candidates
                </button>

                <div className="candidates">
                    {candidates}
                </div>
            </div>
        );
    }
});

var StitchingUI = React.createClass({
    propTypes: {
        client: React.PropTypes.instanceOf(UnshredAPIClient).isRequired
    },
    getInitialState: function() {
        return {
            clusterObj1: null,
            clusterObj2: null
        };
    },
    _setState: function(foo) {
        this.setState(foo);
    },
    render: function() {
        return (
            <div className="stitching">
                <CandidatesTools
                    client={this.props.client}
                    setState={this._setState}
                    />
                <Sandbox
                    client={this.props.client}
                    clusterObj1={this.state.clusterObj1}
                    clusterObj2={this.state.clusterObj2}
                    />
            </div>
            );
    }
});

var client = new UnshredAPIClient("/api");

React.render(
    <StitchingUI client={client} />,
    document.getElementById('stitching')
);
