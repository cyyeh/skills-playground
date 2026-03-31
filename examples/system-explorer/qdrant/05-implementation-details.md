## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Qdrant Quick Start Guide](https://qdrant.tech/documentation/quickstart/) | official-docs
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client) | github
- [Qdrant REST API Reference](https://api.qdrant.tech/) | official-docs
- [Qdrant Source Code](https://github.com/qdrant/qdrant) | github
-->

### Getting Started

**Docker (recommended for production):**
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Python client:**
```bash
pip install qdrant-client
```

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to local Qdrant server
client = QdrantClient(url="http://localhost:6333")

# Create a collection
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Upsert points with vectors and payloads
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, ...],  # 384-dim embedding
            payload={"city": "Berlin", "category": "tech", "price": 299},
        ),
        PointStruct(
            id=2,
            vector=[0.19, 0.81, 0.12, ...],
            payload={"city": "London", "category": "finance", "price": 450},
        ),
    ],
)

# Search with filtering
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, ...],  # query vector
    query_filter={
        "must": [
            {"key": "city", "match": {"value": "Berlin"}},
            {"key": "price", "range": {"lte": 500}},
        ]
    },
    limit=10,
)
```

**Qdrant Cloud (managed):**
```python
client = QdrantClient(
    url="https://xyz-example.us-east.aws.cloud.qdrant.io:6333",
    api_key="<your-api-key>",
)
```

### Configuration Essentials

| Setting | Default | What it controls | When to change |
|---------|---------|-----------------|----------------|
| `vectors.size` | Required | Vector dimensionality | Must match your embedding model |
| `vectors.distance` | Required | Similarity metric (Cosine, Euclid, Dot, Manhattan) | Must match your embedding model |
| `hnsw_config.m` | 16 | HNSW connections per node | Increase to 32-64 for higher recall; decrease for memory savings |
| `hnsw_config.ef_construct` | 100 | Build-time search width | Increase for better graph quality; decrease for faster indexing |
| `hnsw_config.on_disk` | false | Store HNSW graph on disk vs RAM | Enable for large collections that don't fit in RAM |
| `quantization_config` | None | Vector compression (scalar/product/binary) | Enable when memory is constrained; scalar is safest |
| `optimizers_config.indexing_threshold` | 20000 | Points before HNSW index is built | Lower for faster search on small collections |
| `wal_config.wal_capacity_mb` | 32 | WAL file size before rotation | Increase for high-throughput ingestion |
| `replication_factor` | 1 | Number of shard replicas | Increase for fault tolerance in production |
| `shard_number` | 1 | Number of data shards | Increase for distributed deployments |

```python
from qdrant_client.models import (
    VectorParams, Distance, HnswConfigDiff,
    OptimizersConfigDiff, ScalarQuantization, ScalarQuantizationConfig,
    ScalarType,
)

client.create_collection(
    collection_name="production_collection",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True,  # store vectors on disk, keep HNSW in RAM
    ),
    hnsw_config=HnswConfigDiff(m=32, ef_construct=200),
    optimizers_config=OptimizersConfigDiff(
        indexing_threshold=10000,
        memmap_threshold=50000,
    ),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type=ScalarType.INT8,
            quantile=0.99,
            always_ram=True,  # keep quantized vectors in RAM for speed
        ),
    ),
)
```

### Code Patterns

**Batch upsert with named vectors (multi-modal):**
```python
from qdrant_client.models import PointStruct, VectorParams, Distance

# Create collection with multiple named vectors
client.create_collection(
    collection_name="products",
    vectors_config={
        "text": VectorParams(size=384, distance=Distance.COSINE),
        "image": VectorParams(size=512, distance=Distance.COSINE),
    },
)

# Upsert points with both text and image embeddings
client.upsert(
    collection_name="products",
    points=[
        PointStruct(
            id=1,
            vector={
                "text": text_embedding,   # from sentence-transformers
                "image": image_embedding,  # from CLIP
            },
            payload={"name": "Wireless Headphones", "price": 79.99},
        ),
    ],
)

# Search by image similarity
client.query_points(
    collection_name="products",
    query=query_image_embedding,
    using="image",  # search against image vectors
    limit=5,
)
```

**Hybrid search (dense + sparse):**
```python
from qdrant_client.models import SparseVectorParams, SparseIndexParams, models

# Collection with both dense and sparse vectors
client.create_collection(
    collection_name="articles",
    vectors_config={"dense": VectorParams(size=768, distance=Distance.COSINE)},
    sparse_vectors_config={
        "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False)),
    },
)

# Search combining dense (semantic) and sparse (keyword) results
results = client.query_points(
    collection_name="articles",
    prefetch=[
        models.Prefetch(query=dense_vector, using="dense", limit=50),
        models.Prefetch(query=sparse_vector, using="sparse", limit=50),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),  # Reciprocal Rank Fusion
    limit=10,
)
```

**Multi-tenancy with payload-based isolation:**
```python
# Create payload index for tenant isolation
client.create_payload_index(
    collection_name="shared_collection",
    field_name="tenant_id",
    field_schema="keyword",
)

# Each tenant's queries include a mandatory filter
results = client.query_points(
    collection_name="shared_collection",
    query=query_vector,
    query_filter={"must": [{"key": "tenant_id", "match": {"value": "tenant_abc"}}]},
    limit=10,
)
```

### Source Code Walkthrough

#### HNSWIndex -- The Core Index Structure

The `HNSWIndex` struct is the primary vector index in Qdrant, wrapping a multi-layer graph with vector storage, quantization, and payload filtering. Every search operation against a segment with an HNSW index goes through this struct.

```rust
// source: lib/segment/src/index/hnsw_index/hnsw.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub struct HNSWIndex {
    id_tracker: Arc<AtomicRefCell<IdTrackerEnum>>,
    vector_storage: Arc<AtomicRefCell<VectorStorageEnum>>,
    quantized_vectors: Arc<AtomicRefCell<Option<QuantizedVectors>>>,
    payload_index: Arc<AtomicRefCell<StructPayloadIndex>>,
    config: HnswGraphConfig,
    path: PathBuf,
    graph: GraphLayers,
    searches_telemetry: HNSWSearchesTelemetry,
    is_on_disk: bool,
}
```

Note the `Arc<AtomicRefCell<...>>` pattern used throughout -- this provides shared ownership with interior mutability, allowing concurrent reads while serializing writes. The `quantized_vectors` field is optional, populated only when quantization is configured. The `graph: GraphLayers` field holds the actual HNSW graph structure.

#### GraphLayers -- The Multi-Layer HNSW Graph

The `GraphLayers` struct organizes the hierarchical graph with entry points, link storage, and a visited node pool for search operations.

```rust
// source: lib/segment/src/index/hnsw_index/graph_layers.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub struct GraphLayers {
    pub(super) hnsw_m: HnswM,
    pub(super) links: GraphLinks,
    pub(super) entry_points: EntryPoints,
    pub(super) visited_pool: VisitedPool,
}
```

`HnswM` encodes the branching factors: `m` connections at upper layers and `m0 = m * 2` at layer 0. `GraphLinks` stores all neighbor connections in a flattened byte buffer (either in RAM or memory-mapped) with per-point, per-level neighbor lists. `EntryPoints` tracks the highest-level node used as the starting point for searches. `VisitedPool` maintains thread-local visited-node bitsets to prevent re-scoring during beam search.

#### GraphLayers::search -- The Core Search Algorithm

The public `search` method orchestrates the full HNSW search: entry point lookup, greedy descent through upper layers, and beam search at layer 0.

```rust
// source: lib/segment/src/index/hnsw_index/graph_layers.rs
// github: qdrant/qdrant
// tag: v1.17.1

// search_on_level implements beam search at a single layer
fn search_on_level(
    &self,
    level_entry: ScoredPointOffset,
    level: usize,
    ef: usize,
    points_scorer: &mut FilteredScorer,
    is_stopped: &AtomicBool,
) -> CancellableResult<FixedLengthPriorityQueue<ScoredPointOffset>>
```

The `FilteredScorer` is the key integration point: it wraps a distance scorer with a filter check, allowing the beam search to skip non-matching points during traversal without modifying the core HNSW algorithm. The `FixedLengthPriorityQueue` maintains the top-k results efficiently.

#### Distance Metrics -- The QueryScorer Trait

The `QueryScorer` trait defines how similarity scores are computed, supporting both full-precision and quantized vectors.

```rust
// source: lib/segment/src/vector_storage/query_scorer/mod.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub trait QueryScorer {
    type TVector: ?Sized;
    fn score_stored(&self, idx: PointOffsetType) -> ScoreType;
    fn score_stored_batch(&self, ids: &[PointOffsetType], scores: &mut [ScoreType]);
    fn score(&self, v2: &Self::TVector) -> ScoreType;
    fn score_internal(
        &self,
        point_a: PointOffsetType,
        point_b: PointOffsetType,
    ) -> ScoreType;
}
```

The `score_stored` method computes the distance between the query vector and a stored vector by index. The `score_stored_batch` method enables prefetch optimization -- when scoring multiple stored vectors, the implementation can issue CPU prefetch instructions for upcoming memory accesses. The generic `TMetric` parameter allows plugging in different distance functions (Cosine, Euclidean, Dot, Manhattan) without changing the search algorithm.

#### Distance Enum -- Metric Configuration

The `Distance` enum defines the four supported vector comparison metrics, each with different score ordering semantics.

```rust
// source: lib/segment/src/types.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub enum Distance {
    Cosine,
    Euclid,
    Dot,
    Manhattan,
}
```

Cosine and Dot prefer larger scores (more similar = higher score), while Euclidean and Manhattan prefer smaller scores (more similar = shorter distance). Qdrant normalizes Cosine similarity by pre-normalizing vectors at insertion time, making Cosine search equivalent to Dot product search on unit vectors -- an optimization that avoids per-query normalization.

#### Segment -- The Storage Unit

The `Segment` struct is Qdrant's fundamental storage unit, managing vectors, payloads, and indexes for a partition of a collection's data.

```rust
// source: lib/segment/src/segment/mod.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub struct Segment {
    pub uuid: Uuid,
    pub version: Option<SeqNumberType>,
    pub segment_path: PathBuf,
    pub id_tracker: Arc<AtomicRefCell<IdTrackerEnum>>,
    pub vector_data: HashMap<VectorNameBuf, VectorData>,
    pub payload_index: Arc<AtomicRefCell<StructPayloadIndex>>,
    pub payload_storage: Arc<AtomicRefCell<PayloadStorageEnum>>,
    pub appendable_flag: bool,
    pub segment_type: SegmentType,
    pub segment_config: SegmentConfig,
    // ...
}
```

The `vector_data` HashMap maps vector names to `VectorData` structs, each containing the vector index, vector storage, and optional quantized representations. This is how named vectors work: a segment stores independent indexes for each vector name. The `appendable_flag` distinguishes write-optimized segments (accepting new points) from read-optimized segments (HNSW-indexed, immutable).

#### SegmentEntry Trait -- The Segment Interface

Qdrant defines segment capabilities through a trait hierarchy that separates read and write operations.

```rust
// source: lib/segment/src/entry/entry_point.rs
// github: qdrant/qdrant
// tag: v1.17.1

// ReadSegmentEntry: search_batch(), retrieve(), read_filtered(),
//                   read_ordered_filtered(), has_point()
// StorageSegmentEntry: flusher(), drop_data()
// NonAppendableSegmentEntry: delete_point(), build_field_index()
// SegmentEntry: upsert_point(), update_vectors(), set_payload(),
//               delete_payload(), delete_vector()
```

The hierarchy ensures that immutable segments only expose read and delete operations (NonAppendableSegmentEntry) while appendable segments expose full write operations (SegmentEntry). This trait-based design allows the optimizer to work with different segment types polymorphically.

#### LocalShard -- Shard-Level Coordination

The `LocalShard` manages a collection's data on a single node, coordinating WAL, segments, and optimization.

```rust
// source: lib/collection/src/shards/local_shard/mod.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub struct LocalShard {
    collection_name: CollectionId,
    pub(super) segments: LockedSegmentHolder,
    pub(super) wal: RecoverableWal,
    pub(super) update_handler: Arc<Mutex<UpdateHandler>>,
    pub(super) path: PathBuf,
    pub(super) optimizers: ArcSwap<Vec<Arc<Optimizer>>>,
    // ...
}
```

The `LockedSegmentHolder` provides concurrent access to segments without holding locks during data operations. The `ArcSwap` for optimizers allows hot-swapping optimizer configurations without restarting. The WAL (`RecoverableWal`) ensures durability -- on crash recovery, the shard replays uncommitted WAL entries.

#### PayloadStorageEnum -- Storage Backend Selection

Qdrant supports multiple payload storage backends, selected at compile time via feature flags.

```rust
// source: lib/segment/src/payload_storage/payload_storage_enum.rs
// github: qdrant/qdrant
// tag: v1.17.1
pub enum PayloadStorageEnum {
    InMemoryPayloadStorage(InMemoryPayloadStorage),       // testing only
    SimplePayloadStorage(SimplePayloadStorage),           // RocksDB-backed
    OnDiskPayloadStorage(OnDiskPayloadStorage),           // RocksDB on-disk
    MmapPayloadStorage(MmapPayloadStorage),               // Memory-mapped files
}
```

The `MmapPayloadStorage` is unconditionally compiled and provides predictable latency via OS page cache management. The RocksDB-backed variants offer write optimization through LSM-tree compaction. The enum abstraction ensures the rest of the codebase is agnostic to the storage backend.

#### GraphLinks -- HNSW Edge Storage Formats

Qdrant stores HNSW graph connections in different formats optimized for different memory/performance trade-offs.

```rust
// source: lib/segment/src/index/hnsw_index/graph_links.rs
// github: qdrant/qdrant
// tag: v1.17.1

// GraphLinksEnum: storage backends
// - Ram: Vec<u8> -- in-memory byte buffer
// - Mmap: Arc<Mmap> -- memory-mapped file

// GraphLinksFormat: compression formats
// - Plain: uncompressed neighbor lists
// - Compressed: compressed neighbor lists
// - CompressedWithVectors: compressed + inline quantized vectors
```

The `CompressedWithVectors` format (introduced for inline storage in v1.16) embeds quantized vector data directly alongside graph links. During HNSW traversal, this eliminates a cache miss per neighbor -- instead of following a pointer to a separate vector storage area, the quantized vector is read from the same cache line as the neighbor ID. This optimization significantly reduces search latency for quantized collections.

### Deployment Considerations

**Sizing:** For a collection of N vectors with D dimensions: RAM usage ~= N * D * 4 bytes (float32) + N * m * 2 * 8 bytes (HNSW links at layer 0). With scalar quantization, vector RAM drops to N * D bytes. Use mmap storage (`on_disk: true`) for collections that exceed available RAM -- performance depends on SSD speed and OS page cache effectiveness.

**Monitoring:** Qdrant exposes Prometheus metrics at `/metrics` and telemetry via the `/telemetry` API. Key metrics: `search_latency_seconds`, `update_latency_seconds`, `vectors_count`, `segments_count`, `optimizer_status`. Monitor segment count -- too many unoptimized segments indicate the optimizer is falling behind ingestion.

**Backup:** Use the snapshot API (`POST /collections/{name}/snapshots`) to create point-in-time backups. Snapshots include all segments, WAL, and configuration. For distributed deployments, each node must be snapshotted independently or use the collection-level snapshot that coordinates across shards.

**Upgrades:** Qdrant maintains backward-compatible storage formats within minor versions. For major version upgrades, consult the migration guide. The snapshot/restore path provides a safe upgrade mechanism: snapshot on old version, upgrade, restore on new version.

**Concurrency:** Qdrant handles concurrent reads and writes naturally: searches read from indexed (immutable) segments while writes go to the appendable segment. The optimizer's segment replacement is atomic -- search threads never see a partially-built index. For write-heavy workloads, increase `wal_capacity_mb` and consider multiple shards to distribute write load.
