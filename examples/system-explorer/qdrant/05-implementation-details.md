## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Qdrant Quickstart](https://qdrant.tech/documentation/quickstart/) | official-docs
- [Qdrant GitHub Repository](https://github.com/qdrant/qdrant) | github
- [Quantization Documentation](https://qdrant.tech/documentation/manage-data/quantization/) | official-docs
- [Distributed Deployment Guide](https://qdrant.tech/documentation/operations/distributed_deployment/) | official-docs
-->

### Getting Started

The fastest path from zero to a running Qdrant instance is Docker:

```bash
# Pull and run Qdrant with persistent storage
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

This exposes:
- **REST API** at `http://localhost:6333`
- **Web Dashboard** at `http://localhost:6333/dashboard`
- **gRPC API** at `localhost:6334`

Verify it is running:

```bash
curl http://localhost:6333/healthz
```

Install the Python client and create your first collection:

```bash
pip install qdrant-client
```

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")

# Create a collection for 768-dimensional vectors
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)

# Insert points with payloads
client.upsert(
    collection_name="my_collection",
    wait=True,
    points=[
        PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, ...],  # 768 dimensions
            payload={"category": "electronics", "price": 299.99}
        ),
    ],
)

# Search with filtering
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, ...],  # query vector
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="electronics")),
            FieldCondition(key="price", range=Range(lte=500.0)),
        ]
    ),
    limit=10,
).points
```

### Configuration Essentials

Qdrant's configuration is YAML-based (`config/config.yaml`). The most critical knobs for production:

| Parameter | Default | What It Controls | When to Change |
|-----------|---------|-----------------|----------------|
| `storage.performance.optimizers_threads` | auto | CPU threads for background optimization | Limit on shared machines to avoid starving search threads |
| `storage.hnsw_index.m` | 16 | HNSW edges per node | Increase to 32-64 for high-recall requirements; decrease for memory savings |
| `storage.hnsw_index.ef_construct` | 100 | Construction search width | Increase to 200+ for better index quality at the cost of build time |
| `storage.hnsw_index.full_scan_threshold` | 10000 | Points below which brute-force beats HNSW | Lower for collections with many small filtered subsets |
| `storage.on_disk_payload` | false | Store payloads on disk vs RAM | Enable for large payloads to reduce RAM usage |
| `cluster.enabled` | false | Distributed mode | Enable for multi-node deployments |
| `cluster.p2p.port` | 6335 | Inter-node communication port | Must be accessible between all cluster peers |
| `storage.quantization.always_ram` | false | Keep quantized vectors in RAM | Enable in production for optimal search speed with quantization |
| `storage.wal.wal_capacity_mb` | 32 | WAL file size before rotation | Increase for write-heavy workloads to reduce rotation frequency |
| `service.max_request_size_mb` | 32 | Max request body size | Increase for large batch upserts |

Example production configuration snippet:

```yaml
storage:
  storage_path: /qdrant/storage
  performance:
    optimizers_threads: 4
  hnsw_index:
    m: 16
    ef_construct: 128
    full_scan_threshold: 10000
  on_disk_payload: true
  quantization:
    always_ram: true

cluster:
  enabled: true
  p2p:
    port: 6335
  consensus:
    tick_period_ms: 100
```

### Code Patterns

**Hybrid search (dense + sparse vectors):**

```python
from qdrant_client.models import (
    SparseVector, NamedSparseVector, SearchRequest, 
    Prefetch, FusionQuery, Fusion
)

# Create collection with both dense and sparse vectors
client.create_collection(
    collection_name="hybrid_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    sparse_vectors_config={
        "text-sparse": {}
    },
)

# Hybrid search: combine dense and sparse results using RRF
results = client.query_points(
    collection_name="hybrid_collection",
    prefetch=[
        Prefetch(query=[0.1, 0.2, ...], using="", limit=20),  # dense
        Prefetch(
            query=SparseVector(indices=[1, 42, 77], values=[0.5, 0.8, 0.3]),
            using="text-sparse",
            limit=20,
        ),  # sparse
    ],
    query=FusionQuery(fusion=Fusion.RRF),  # reciprocal rank fusion
    limit=10,
)
```

**Batch upsert with progress tracking:**

```python
import numpy as np
from qdrant_client.models import PointStruct, UpdateStatus

BATCH_SIZE = 100
vectors = np.random.rand(10000, 768).tolist()

for i in range(0, len(vectors), BATCH_SIZE):
    batch = [
        PointStruct(id=j, vector=vectors[j], payload={"batch": i // BATCH_SIZE})
        for j in range(i, min(i + BATCH_SIZE, len(vectors)))
    ]
    result = client.upsert(
        collection_name="my_collection",
        wait=True,
        points=batch,
    )
    assert result.status == UpdateStatus.COMPLETED
```

**Scroll through all points (pagination):**

```python
offset = None
all_points = []

while True:
    result, offset = client.scroll(
        collection_name="my_collection",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )
    all_points.extend(result)
    if offset is None:
        break
```

### Source Code Walkthrough

The following source code excerpts are from Qdrant's Rust codebase and implement the core concepts and architectural components described in earlier sections.

#### HNSW Graph Layers -- Implementation

The `GraphLayers` struct is the core data structure behind the HNSW Index concept. It stores the multi-layered graph where each vector is a node with connections to its nearest neighbors. The `search` method implements the two-phase greedy traversal: descending through upper layers to find the entry region, then performing a wider neighborhood search at the base layer.

```rust
// source: lib/segment/src/index/hnsw_index/graph_layers.rs:1-30
// github: qdrant/qdrant
// tag: v1.13.2
pub struct GraphLayers {
    pub(super) m: usize,
    pub(super) m0: usize,
    pub(super) links: GraphLinks,
    pub(super) entry_points: EntryPoints,
    pub(super) visited_pool: VisitedPool,
}

impl GraphLayers {
    pub fn search(
        &self,
        top: usize,
        ef: usize,
        mut points_scorer: FilteredScorer,
        custom_entry_points: Option<&[PointOffsetType]>,
    ) -> Vec<ScoredPointOffset> {
        // Phase 1: locate optimal entry point via greedy descent
        let entry = self.search_entry(&mut points_scorer, custom_entry_points);
        // Phase 2: neighborhood exploration at base layer with beam width ef
        self.search_on_level(entry, top, ef, &mut points_scorer, 0)
    }

    fn get_m(&self, level: usize) -> usize {
        if level == 0 { self.m0 } else { self.m }
    }
}
```

Notice how `m0` (base layer) has more connections than `m` (upper layers). The base layer is where final results are found, so denser connectivity improves recall. The `FilteredScorer` parameter enables the filterable HNSW approach -- the scorer can skip points that do not match payload filters while still using their graph links for traversal.

#### HNSW Graph Construction -- Implementation

The `GraphLayersBuilder` implements the parallel graph construction algorithm. The `link_new_point` method shows how each new vector is integrated into the multi-layered graph, and `select_candidate_with_heuristic_from_sorted` implements the neighbor selection heuristic that prevents redundant short-range links.

```rust
// source: lib/segment/src/index/hnsw_index/graph_layers_builder.rs:1-40
// github: qdrant/qdrant
// tag: v1.13.2
pub struct GraphLayersBuilder {
    max_level: AtomicUsize,
    m: usize,
    m0: usize,
    ef_construct: usize,
    level_factor: f64,
    use_heuristic: bool,
    links_layers: Vec<LockedLayersContainer>,
    entry_points: Mutex<EntryPoints>,
    visited_pool: VisitedPool,
    ready_list: RwLock<BitVec>,
}

impl GraphLayersBuilder {
    /// Integrates a new vector into the HNSW graph at all relevant levels
    pub fn link_new_point(
        &self,
        point_id: PointOffsetType,
        mut points_scorer: FilteredScorer,
    ) {
        // Discover entry points, then iteratively connect at each level
        // from highest to lowest, using ef_construct neighbors
    }

    /// Heuristic neighbor selection: rejects candidates whose distance to
    /// already-selected neighbors exceeds their distance to the query,
    /// preventing redundant short-range links and promoting diversity
    fn select_candidate_with_heuristic_from_sorted<F>(
        candidates: impl Iterator<Item = ScoredPointOffset>,
        m: usize,
        mut score_internal: F,
    ) -> Vec<PointOffsetType> {
        // For each candidate, check if it is closer to the query than
        // to any already-selected neighbor -- if so, keep it
    }
}
```

The `ready_list` (a bit vector) tracks which points have been fully inserted and are safe for concurrent readers to traverse. The `AtomicUsize` for `max_level` and the `Mutex` on entry points enable lock-free reading during parallel construction.

#### Core Type Definitions -- Point and Vector Types

The `types.rs` file defines the foundational data structures that map directly to the Core Concepts. `ScoredPoint` is what search results look like, `VectorDataConfig` defines how vectors are stored, and `Filter` implements the payload filtering system.

```rust
// source: lib/segment/src/types.rs:1-60
// github: qdrant/qdrant
// tag: v1.13.2

/// A search result: the point, its score, and optional metadata
pub struct ScoredPoint {
    pub id: PointIdType,
    pub version: SeqNumberType,
    pub score: ScoreType,
    pub payload: Option<Payload>,
    pub vector: Option<VectorStructInternal>,
    pub shard_key: Option<ShardKey>,
    pub order_value: Option<OrderValue>,
}

/// Configuration for a single vector field in a collection
pub struct VectorDataConfig {
    pub size: usize,                    // dimensionality
    pub distance: Distance,             // Cosine, Euclid, Dot, Manhattan
    pub storage_type: VectorStorageType, // Memory, Mmap, ChunkedMmap
    pub index: Indexes,                 // Plain or Hnsw
    pub quantization_config: Option<QuantizationConfig>,
    pub multivector_config: Option<MultiVectorConfig>,
    pub datatype: Option<VectorStorageDatatype>,
}

/// Complex filter with boolean logic
pub struct Filter {
    pub should: Option<Vec<Condition>>,   // OR
    pub must: Option<Vec<Condition>>,     // AND
    pub must_not: Option<Vec<Condition>>, // NOT
    pub min_should: Option<MinShould>,    // at-least-N-of
}

/// Distance metrics for similarity computation
pub enum Distance {
    Cosine,
    Euclid,
    Dot,
    Manhattan,
}

/// Quantization strategy selection
pub enum QuantizationConfig {
    Scalar(ScalarQuantizationConfig),
    Product(ProductQuantizationConfig),
    Binary(BinaryQuantizationConfig),
}
```

The `Distance` enum directly maps to the distance metric chosen at collection creation time. The `Filter` struct with `should`/`must`/`must_not` mirrors Elasticsearch's boolean query syntax, making it familiar to engineers coming from document search backgrounds.

#### SegmentEntry Trait -- The Segment Interface

The `SegmentEntry` trait defines the contract that all segment types (mutable and immutable) must implement. This is the core abstraction that allows the segment holder to treat all segments uniformly -- search, upsert, delete, and index operations all go through this interface.

```rust
// source: lib/segment/src/entry/entry_point.rs:1-50
// github: qdrant/qdrant
// tag: v1.13.2

/// Define all operations which can be performed with Segment or
/// Segment-like entity. Assume all operations are idempotent.
pub trait SegmentEntry {
    // --- Version Management ---
    fn version(&self) -> SeqNumberType;
    fn point_version(&self, point_id: PointIdType) -> Option<SeqNumberType>;

    // --- Search Operations ---
    fn search_batch(
        &self,
        vector_name: &VectorName,
        query_vectors: &[&QueryVector],
        with_payload: &WithPayload,
        with_vector: &WithVector,
        filter: Option<&Filter>,
        top: usize,
        params: Option<&SearchParams>,
    ) -> OperationResult<Vec<Vec<ScoredPoint>>>;

    fn read_filtered(
        &self,
        offset: Option<PointIdType>,
        limit: Option<usize>,
        filter: Option<&Filter>,
    ) -> Vec<PointIdType>;

    // --- Data Modification ---
    fn upsert_point(
        &self,
        op_num: SeqNumberType,
        point_id: PointIdType,
        vectors: NamedVectors,
    ) -> OperationResult<bool>;

    fn delete_point(
        &self,
        op_num: SeqNumberType,
        point_id: PointIdType,
    ) -> OperationResult<bool>;

    // --- Payload Management ---
    fn set_payload(
        &self,
        op_num: SeqNumberType,
        point_id: PointIdType,
        payload: &Payload,
        key: &Option<JsonPath>,
    ) -> OperationResult<bool>;

    // --- Persistence ---
    fn flush(&self, sync: bool) -> OperationResult<SeqNumberType>;
    fn take_snapshot(&self, snapshot_dir: &Path) -> OperationResult<PathBuf>;
}
```

The `op_num: SeqNumberType` parameter on every write method is the WAL sequence number. This enables idempotent replay during crash recovery -- if a segment already has a version equal to or higher than `op_num`, the operation is safely skipped.

#### Replica Set -- Distributed Shard Management

The `ShardReplicaSet` manages replicas of a single shard across cluster nodes. Its state machine (9 distinct replica states) and the split between local and remote replicas reveal how Qdrant handles distributed read/write routing.

```rust
// source: lib/collection/src/shards/replica_set/mod.rs:1-50
// github: qdrant/qdrant
// tag: v1.13.2

pub struct ShardReplicaSet {
    local: RwLock<Option<Shard>>,           // local replica, if present
    remotes: RwLock<Vec<RemoteShard>>,       // connections to peer replicas
    replica_state: Arc<SaveOnDisk<ReplicaSetState>>,
    locally_disabled_peers: parking_lot::RwLock<Registry>,
    write_rate_limiter: Option<parking_lot::Mutex<RateLimiter>>,
    write_ordering_lock: Mutex<()>,          // serializes ordered writes
    // ... consensus callbacks, clock set, runtime handles
}

/// Replica lifecycle states
pub enum ReplicaState {
    Active,          // fully operational
    Dead,            // failed or unreachable
    Partial,         // receiving data from peers
    Initializing,    // collection creation in progress
    Listener,        // receives data, excluded from search
    PartialSnapshot, // legacy snapshot transfer
    Recovery,        // external recovery in progress
    Resharding,      // receiving migrated points (scale up)
    ReshardingScaleDown, // receiving migrated points (scale down)
}
```

The read path prefers the local `Shard` for lowest latency, falling back to remote shards only when the local replica is unavailable or read consistency requires quorum. The `locally_disabled_peers` registry allows a node to temporarily exclude a peer it has observed as failing, without waiting for Raft consensus to formally mark it as Dead -- this speeds up failure detection.

#### Collection Search -- Distributed Query Coordination

The collection's search implementation shows how queries fan out to shards and merge results. The two-phase payload optimization (search first for IDs/scores, then fetch payloads separately when the transfer cost exceeds a threshold) is a key performance detail.

```rust
// source: lib/collection/src/collection/search.rs:1-40
// github: qdrant/qdrant
// tag: v1.13.2

impl Collection {
    /// Execute a batch of search requests across all relevant shards
    pub async fn core_search_batch(
        &self,
        request: CoreSearchRequestBatch,
        read_consistency: Option<ReadConsistency>,
        shard_selection: &ShardSelectorInternal,
        timeout: Option<Duration>,
    ) -> CollectionResult<Vec<Vec<ScoredPoint>>> {
        // Fan out to all matching shards concurrently
        let shard_results = future::try_join_all(
            shards.iter().map(|shard| shard.search(request.clone()))
        ).await?;

        // Merge results from all shards using k-way merge
        merge_from_shards(shard_results, request.limit, request.offset)
    }
}

/// Merge search results from multiple shards, deduplicating by point ID
fn merge_from_shards(
    shard_results: Vec<Vec<Vec<ScoredPoint>>>,
    limit: usize,
    offset: usize,
) -> Vec<Vec<ScoredPoint>> {
    // K-way merge respecting distance ordering
    // Deduplicate by point ID, keeping highest-versioned result
    // Apply offset/limit after merge
}
```

#### Segment Searcher -- Multi-Segment Fan-Out

The `SegmentsSearcher` shows how queries are distributed across segments within a single shard. The probabilistic sampling optimization and adaptive re-search are key to maintaining low latency when many segments exist.

```rust
// source: lib/collection/src/collection_manager/segments_searcher.rs:1-40
// github: qdrant/qdrant
// tag: v1.13.2

impl SegmentsSearcher {
    /// Search across all segments in a shard with adaptive sampling
    pub async fn search(
        &self,
        request: &CoreSearchRequest,
    ) -> CollectionResult<Vec<ScoredPoint>> {
        // Phase 1: Probabilistic sampling
        // Determine a smaller sampling limit per segment based on
        // each segment's proportion of total points
        let initial_results = self.execute_searches(
            segments, sampling_limits, request
        ).await?;

        // Phase 2: Adaptive re-search
        // If any segment's lowest score exceeds the batch minimum
        // but hasn't returned enough results, re-search without
        // sampling constraints
        let refined_results = self.process_search_result_step1(
            initial_results, request.limit
        );

        // Merge across segments, resolving version conflicts
        BatchResultAggregator::merge(refined_results)
    }
}
```

The probabilistic sampling avoids over-fetching from each segment. If a shard has 5 segments and you need 10 results, searching each segment for 10 results produces 50 candidates (most discarded). Sampling estimates how many results each segment is likely to contribute and adjusts per-segment limits accordingly.

### Deployment Considerations

**Sizing.** Memory is the primary constraint. Estimate RAM as: `num_vectors * vector_dimensions * bytes_per_dimension`. For 100M vectors at 768 dimensions with float32: ~286 GB. With scalar quantization: ~72 GB. With binary quantization: ~9 GB (plus HNSW graph overhead of ~1-2 bytes per vector per edge).

**Monitoring.** Qdrant exposes Prometheus metrics at `/metrics`. Key metrics to monitor:
- `qdrant_search_latency_seconds` -- p50/p95/p99 search latency
- `qdrant_segments_count` -- number of segments per collection (many segments = optimizer behind)
- `qdrant_points_count` -- total points per collection
- `qdrant_optimizer_status` -- whether optimization is running or stalled

**Backup and Recovery.** Use snapshot APIs to create point-in-time backups:
```bash
# Create a snapshot
curl -X POST "http://localhost:6333/collections/my_collection/snapshots"

# List snapshots
curl "http://localhost:6333/collections/my_collection/snapshots"

# Restore from snapshot
curl -X PUT "http://localhost:6333/collections/my_collection/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d '{"location": "/path/to/snapshot.snapshot"}'
```

**Cluster deployment.** For production, use a minimum of 3 nodes with replication factor 2+. Configure `write_consistency_factor` based on your durability requirements. Use Kubernetes with the [official Helm chart](https://github.com/qdrant/qdrant-helm) for orchestrated deployments:

```bash
helm repo add qdrant https://qdrant.to/helm
helm install qdrant qdrant/qdrant --set cluster.enabled=true --set replicaCount=3
```

**Upgrade path.** Qdrant supports rolling upgrades within minor versions. For major version upgrades, take a full snapshot before upgrading. The Qdrant team maintains backward compatibility for the REST API and storage format within major versions.
