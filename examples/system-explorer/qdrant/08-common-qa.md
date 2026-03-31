## Common Q&A
<!-- level: all -->
<!-- references:
- [Capacity Planning](https://qdrant.tech/documentation/guides/capacity-planning/) | docs
- [Database Optimization FAQ](https://qdrant.tech/documentation/faq/database-optimization/) | docs
- [Minimal RAM for a Million Vectors](https://qdrant.tech/articles/memory-consumption/) | blog
- [Scaling Qdrant Cloud Clusters](https://qdrant.tech/documentation/cloud/cluster-scaling/) | docs
- [Large-Scale Data Ingestion](https://qdrant.tech/course/essentials/day-4/large-scale-ingestion/) | course
- [Distributed Deployment](https://qdrant.tech/documentation/operations/distributed_deployment/) | docs
-->

### Q1: How much memory does Qdrant need for N vectors?

**Rule of thumb:** `memory_bytes = num_vectors x vector_dimensions x 4 x 1.5`

The factor of 4 accounts for 32-bit floats, and the 1.5 multiplier covers HNSW graph overhead, metadata, and temporary segments during optimization.

**Example:** 10 million vectors at 768 dimensions = 10M x 768 x 4 x 1.5 = ~46 GB RAM.

**To reduce memory:**
- Use mmap storage (`on_disk=True`) — vectors live on disk, OS caches hot data
- Enable scalar quantization — reduces to ~12 GB (4x compression)
- Enable binary quantization — reduces to ~1.4 GB (32x compression), but only suitable for certain embedding models
- Use product quantization — variable compression (4x-64x)

With mmap + scalar quantization (quantized vectors in RAM, originals on disk), you can serve 10M vectors with ~3 GB of RAM for the quantized index plus OS cache for rescoring.

### Q2: How do I scale Qdrant for growing data?

**Vertical scaling (single node):**
- Add more RAM for faster search
- Use faster NVMe SSDs for mmap-backed storage
- Increase CPU cores (Qdrant parallelizes search across threads)

**Horizontal scaling (cluster):**
- Start with more shards than current nodes (e.g., 12 shards on 3 nodes)
- Scale by adding nodes — Qdrant will rebalance shards automatically
- Increase replication factor for read throughput and fault tolerance

**Scaling tip:** Start with shard_number = 12. This allows scaling from 1 node up to 2, 3, 4, 6, or 12 nodes without resharding. Resharding an existing collection requires creating a new collection and re-ingesting data.

### Q3: What consistency guarantees does Qdrant provide?

In **single-node mode**, Qdrant provides strong consistency — reads always see the latest writes after the WAL is flushed.

In **distributed mode**, consistency is configurable per operation:
- `factor: 1` — Write to one replica, fastest but eventual consistency
- `factor: majority` — Write to majority of replicas before ACK
- `factor: all` — Write to all replicas, strongest consistency, highest latency
- `factor: quorum` — Write to quorum of replicas

For reads, you can set `consistency` to control how many replicas must agree. Default is eventual consistency (read from any replica).

**Important:** Qdrant does NOT support multi-document ACID transactions. Each point operation is atomic, but there is no way to atomically update multiple points across collections.

### Q4: How do I handle multi-tenancy?

Three approaches, from simplest to most scalable:

1. **Payload-based filtering** — Store a `tenant_id` field in each point's payload and filter on it. Simplest to implement, but all tenants share the same HNSW graph, which can reduce search efficiency for narrow tenant filters.

2. **Collection-per-tenant** — Create a separate collection for each tenant. Clean isolation, but many collections create operational overhead and prevent cross-tenant searches.

3. **Custom sharding** — Use Qdrant's custom shard keys with tenant IDs. Each tenant's data goes to a dedicated shard. Searches are routed only to the relevant shard, combining isolation with efficient search. This is the recommended approach for most multi-tenant deployments. Qdrant v1.16 introduced tiered multitenancy to further optimize this pattern.

### Q5: What happens when a node goes down in a cluster?

With `replication_factor >= 2`:
- Reads continue from surviving replicas with no user-visible impact
- Writes with `consistency: 1` continue immediately; writes requiring majority/all consistency will wait or fail depending on the number of surviving replicas
- When the node recovers, Qdrant automatically synchronizes the replica using WAL-based catch-up
- If the node is permanently lost, a new replica can be created on a different node via the cluster API

Shard transfer during rebalancing uses streaming, and the source shard remains available for reads during the transfer.

### Q6: How do I migrate from another vector database?

**From Pinecone, Weaviate, Milvus, or Chroma:**
1. Export vectors and metadata from the source database
2. Transform into Qdrant's point format (ID + vector + payload)
3. Use batch upsert with the Python client (`upload_points` for <1M, `upload_collection` for >1M)
4. Create payload indexes for fields you'll filter on
5. Verify with test queries

**From pgvector:**
1. Query vectors from PostgreSQL
2. Stream into Qdrant using batch upsert
3. Re-create any index/filter logic as payload indexes

**Tips:**
- Disable indexing during bulk upload by setting a high `indexing_threshold`, then lower it after upload completes
- Use parallel upload workers (the Python client supports async operations)
- Monitor the optimizer status — wait for all segments to be indexed before benchmarking

### Q7: How do I tune search accuracy vs. latency?

Three levers to adjust:

1. **HNSW `ef` (query-time)** — Higher values explore more candidates, improving recall but increasing latency. Start with `ef=128`, increase if recall is insufficient.

2. **HNSW `m` (build-time)** — More edges per node improves graph connectivity and recall. Typical range: 16-64. Higher values also increase memory and build time.

3. **Quantization + oversampling** — Enable quantization for speed, then use `oversampling` (e.g., 2.0) to retrieve extra candidates and rescore with full-precision vectors.

**Benchmarking tip:** Use Qdrant's built-in `/collections/{name}/points/search` with `with_vector: false` and measure latency at different `ef` values. Plot the recall-latency curve to find your sweet spot.

### Q8: Can I use GPU acceleration with Qdrant?

Yes. Qdrant supports GPU-accelerated vector search using NVIDIA GPUs. GPU acceleration is most beneficial for:
- Very large collections (tens of millions of vectors or more)
- High query throughput requirements
- Batch search operations

GPU support is available via dedicated Docker images and requires NVIDIA drivers and CUDA toolkit. It accelerates distance calculations during HNSW traversal but does not replace CPU-based index construction.

### Q9: How do I handle vector updates and versioning?

- **Overwrite by ID** — Upserting a point with an existing ID replaces the vector and payload. This is the simplest approach for updates.
- **Payload-only updates** — Use `set_payload` to update metadata without touching the vector.
- **Soft deletes** — Add a `version` or `deleted` field to payloads and filter accordingly. The old vectors are eventually removed by the vacuum optimizer.
- **Collection aliases** — For blue-green deployments, build a new collection, then atomically swap the alias to point to it. Zero downtime.

### Q10: What are the operational gotchas to watch for?

1. **Optimization backlog** — After large bulk uploads, HNSW index building can take significant time and memory. Monitor optimizer status and don't benchmark during active optimization.
2. **Memory spikes during optimization** — Segment merging temporarily doubles memory usage. Ensure headroom.
3. **WAL growth** — Under heavy write load, WAL can grow large if the flush worker falls behind. Monitor WAL size.
4. **Shard count is immutable** — You cannot change shard_number after collection creation. Plan ahead.
5. **Payload index memory** — Each indexed payload field consumes memory. Only index fields used in filters.
6. **gRPC version compatibility** — v1.17 changed the gRPC response format for vectors. Ensure client libraries are updated before upgrading.
