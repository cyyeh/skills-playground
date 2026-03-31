## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Qdrant Quickstart](https://qdrant.tech/documentation/quickstart/) | docs
- [API & SDKs](https://qdrant.tech/documentation/interfaces/) | docs
- [Installation](https://qdrant.tech/documentation/operations/installation/) | docs
- [Capacity Planning](https://qdrant.tech/documentation/guides/capacity-planning/) | docs
- [Database Optimization](https://qdrant.tech/documentation/faq/database-optimization/) | docs
- [Optimizing Memory for Bulk Uploads](https://qdrant.tech/articles/indexing-optimization/) | blog
-->

### Getting Started

The fastest way to run Qdrant locally is via Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
  qdrant/qdrant
```

This exposes the REST API on port 6333 and gRPC on port 6334, with data persisted to a local directory.

### REST API Examples

**Create a collection:**
```bash
curl -X PUT http://localhost:6333/collections/my_collection \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'
```

**Upsert points:**
```bash
curl -X PUT http://localhost:6333/collections/my_collection/points \
  -H 'Content-Type: application/json' \
  -d '{
    "points": [
      {
        "id": 1,
        "vector": [0.1, 0.2, ...],
        "payload": {"city": "Berlin", "category": "tech"}
      }
    ]
  }'
```

**Search with filter:**
```bash
curl -X POST http://localhost:6333/collections/my_collection/points/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": [0.1, 0.2, ...],
    "filter": {
      "must": [{"key": "city", "match": {"value": "Berlin"}}]
    },
    "limit": 10
  }'
```

### Python Client

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)

# Upsert points
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],
            payload={"city": "Berlin", "category": "tech"},
        ),
    ],
)

# Search with filter
results = client.query_points(
    collection_name="my_collection",
    query=[0.1, 0.2, ...],
    query_filter=models.Filter(
        must=[models.FieldCondition(key="city", match=models.MatchValue(value="Berlin"))]
    ),
    limit=10,
)
```

For production workloads, use gRPC for lower latency:
```python
client = QdrantClient(url="http://localhost:6334", prefer_grpc=True)
```

### Client Libraries

Official SDKs are available for six languages:

| Language | Package | Protocol |
|----------|---------|----------|
| Python | `qdrant-client` | REST + gRPC |
| JavaScript/TypeScript | `@qdrant/js-client-rest` | REST |
| Rust | `qdrant-client` (crate) | gRPC |
| Go | `github.com/qdrant/go-client` | gRPC |
| Java | `io.qdrant:client` | gRPC |
| .NET/C# | `Qdrant.Client` | gRPC |

### Configuration

Qdrant is configured via `config.yaml` or environment variables. Key settings:

```yaml
storage:
  storage_path: ./storage          # Where data lives on disk
  performance:
    max_search_threads: 0          # 0 = auto (CPU count)
    max_optimization_threads: 1

service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334

cluster:
  enabled: false                   # Set true for distributed mode
  p2p:
    port: 6335

optimizers:
  default_segment_number: 0        # 0 = auto
  max_segment_size_kb: 0           # 0 = no limit
  memmap_threshold_kb: 200000      # Switch to mmap above this size
  indexing_threshold_kb: 20000     # Build HNSW above this size
  flush_interval_sec: 5            # Disk flush frequency
```

Environment variable overrides follow the pattern `QDRANT__<SECTION>__<KEY>`, e.g., `QDRANT__SERVICE__HTTP_PORT=6333`.

### Collection Configuration

Key parameters when creating a collection:

```python
client.create_collection(
    collection_name="production",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True,                # Store vectors on disk (mmap)
    ),
    hnsw_config=models.HnswConfigDiff(
        m=16,                        # Edges per node
        ef_construct=100,            # Build-time candidate list
        full_scan_threshold=10000,   # Below this, skip HNSW
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,         # Keep quantized vectors in RAM
        ),
    ),
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,
    ),
    shard_number=6,                  # Number of shards
    replication_factor=2,            # Copies per shard
)
```

### Deployment Options

**Docker Compose (single node with monitoring):**
```yaml
services:
  qdrant:
    image: qdrant/qdrant:v1.17.1
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__CLUSTER__ENABLED: "false"
```

**Kubernetes (Helm chart for distributed cluster):**
```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm install qdrant qdrant/qdrant \
  --set replicaCount=3 \
  --set config.cluster.enabled=true
```

**Qdrant Cloud:** Fully managed service available on AWS, GCP, and Azure with a free 1GB tier requiring no credit card.

### Performance Tuning Guide

**Memory estimation formula:**
```
memory_size = num_vectors × vector_dimension × 4 bytes × 1.5
```
The 1.5 multiplier accounts for metadata, HNSW graph overhead, and temporary segments during optimization.

**Key tuning strategies:**

1. **Use mmap for large collections** — Set `on_disk=True` for vector storage. The OS cache will keep hot vectors in RAM.
2. **Enable quantization** — Scalar quantization (INT8) provides 4x compression with minimal accuracy loss. Keep quantized vectors in RAM (`always_ram=True`) and original vectors on disk.
3. **Tune HNSW parameters** — Start with `m=16, ef_construct=100`. Increase `m` for higher recall, increase `ef` at query time for accuracy.
4. **Index payload fields** — Only fields used in filters should be indexed. Each index consumes memory.
5. **Batch ingestion** — Use batch sizes of 1,000-10,000 for optimal throughput. For >1M points, use `upload_collection` for streaming from disk.
6. **Shard planning** — Start with a shard count that divides evenly into your anticipated node counts (e.g., 12 shards for flexibility with 1, 2, 3, 6, or 12 nodes).

### Monitoring

Qdrant exposes Prometheus metrics at `/metrics` and provides a built-in web dashboard at the REST API root. Key metrics to monitor:

- `qdrant_collections_total` — Number of active collections
- `qdrant_points_total` — Total indexed points across all collections
- `qdrant_search_latency_seconds` — Search latency histograms
- `qdrant_grpc_responses_total` — gRPC request counts by status
- Segment optimizer status — Pending optimizations indicate indexing backlog
