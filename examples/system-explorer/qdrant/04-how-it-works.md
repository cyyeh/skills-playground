## How It Works
<!-- level: intermediate -->
<!-- references:
- [Qdrant Storage Documentation](https://qdrant.tech/documentation/manage-data/storage/) | official-docs
- [HNSW Indexing Fundamentals](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | official-docs
- [Qdrant Quickstart](https://qdrant.tech/documentation/quickstart/) | official-docs
- [Payload Indexing and Filtering (DeepWiki)](https://deepwiki.com/qdrant/qdrant/4-payload-indexing-and-filtering) | wiki
-->

### Indexing Vectors: From Upsert to Searchable

When you upsert points into Qdrant, the data goes through a carefully orchestrated pipeline designed to balance write speed with search performance.

**Step 1 — WAL Persistence.** The operation is first written to the Write-Ahead Log (WAL). Each operation receives a sequential version number. The WAL write must succeed before any acknowledgment is sent to the client, ensuring durability even if the process crashes immediately after.

**Step 2 — Segment Write.** The update worker reads the operation from WAL and applies it to the current appendable (plain) segment. The point's vector is stored in the segment's vector storage, the payload is written to payload storage, and the ID mapping is recorded. Plain segments use simple sequential storage without an HNSW index — incoming points are immediately available for brute-force search but not yet for fast indexed search.

**Step 3 — Optimizer Trigger.** When the appendable segment reaches the indexing threshold (default: 10,000 points), the optimize worker kicks in. It creates a new appendable segment for incoming writes, then converts the full segment to an indexed (non-appendable) segment. During this conversion:
- Vectors are reorganized into optimized storage (optionally memmap).
- The HNSW graph is constructed, connecting each vector to its nearest neighbors across multiple layers.
- Payload field indexes are built for any fields configured for indexing.
- The segment is sealed — it becomes immutable for inserts but still supports deletes and reads.

**Step 4 — Periodic Flush.** The flush worker persists segment state to disk every 5 seconds (configurable), ensuring that even non-WAL data (like index structures) is durably stored.

### How HNSW Search Works

When a search query arrives, Qdrant navigates the HNSW graph to find the approximate nearest neighbors efficiently.

**Step 1 — Entry Point.** The search begins at the top layer of the HNSW graph, which contains very few nodes with long-range connections. An entry point node is selected.

**Step 2 — Greedy Descent.** At each layer, the algorithm greedily moves to the neighbor closest to the query vector. This is like navigating highway-level connections to quickly reach the right "neighborhood" of the vector space.

**Step 3 — Layer Transition.** Once the algorithm can no longer find a closer neighbor at the current layer, it drops down to the next layer, which has more nodes and shorter-range connections. The search becomes more fine-grained.

**Step 4 — Bottom Layer Search.** At the bottom layer (layer 0), which contains all points, the algorithm maintains a priority queue of the `ef` best candidates (configurable at query time). It explores neighbors of candidates, adding better matches to the queue until no further improvements are found.

**Step 5 — Result Ranking.** The top-k candidates from the priority queue are returned, ranked by their distance to the query vector according to the collection's distance metric.

The `ef` parameter controls the accuracy-speed trade-off at search time. Higher `ef` values explore more candidates, yielding better recall at the cost of higher latency. Typical production values range from 64 to 256.

### Filtered Search

Filtered search in Qdrant combines vector similarity with payload conditions. Importantly, filtering is integrated into the HNSW traversal rather than applied as a separate post-processing step.

**Small Filter Result Sets:** When the filter is very selective (matching a small fraction of points), Qdrant may bypass HNSW entirely and perform a filtered brute-force scan over matching points. This avoids the overhead of graph traversal when most graph nodes would be filtered out anyway.

**Large Filter Result Sets:** When the filter matches a significant portion of points, Qdrant traverses the HNSW graph normally but checks each candidate against the filter conditions. Points that fail the filter are skipped, and the algorithm continues exploring. The ACORN algorithm (introduced in 2025) improves efficiency for filtered HNSW queries by considering filter conditions during graph navigation.

**Payload Index Types:** For efficient filtering, Qdrant supports several index types on payload fields:
- **Keyword index:** For exact string matching and `in` conditions.
- **Integer/Float index:** For numeric range queries.
- **Geo index:** For geographic radius and bounding box queries.
- **Full-text index:** For text search using tokenized inverted indexes.
- **Datetime index:** For temporal range queries.
- **UUID index:** For UUID field matching.

### Snapshot and Recovery

Qdrant provides snapshot mechanisms for backup, migration, and disaster recovery.

**Creating Snapshots:** A snapshot captures the complete state of a collection (or the entire Qdrant instance) at a point in time. This includes all segments with their vectors, payloads, indexes, and the WAL. Snapshots are created as compressed archive files.

**Recovery from WAL:** On normal startup after a clean shutdown, Qdrant loads segments from disk. After an abnormal shutdown (crash, power loss), Qdrant loads the last flushed segment state and replays WAL entries. The version tracking on each point ensures idempotent replay — operations with version numbers lower than the current point version are safely skipped.

**Snapshot Recovery:** A collection can be restored from a snapshot file, which replaces all current data and indexes. In distributed mode, the Collection Snapshot Recovery API can restore missing shards on new or replacement nodes.

**Shard Transfer for Recovery:** In a cluster, if a node permanently fails, its shards can be replicated to a new node using one of three transfer methods: `stream_records` (rebuilds indexes), `snapshot` (transfers full snapshot including indexes), or `wal_delta` (incremental sync for partially recovered shards).
