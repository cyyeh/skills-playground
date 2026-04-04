## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [How vLLM Accelerates AI Inference: 3 Enterprise Use Cases](https://www.redhat.com/en/topics/ai/how-vllm-accelerates-ai-inference-3-enterprise-use-cases) | blog
- [vLLM Production Stack](https://github.com/vllm-project/production-stack) | github
- [vLLM Production Deployment Architecture](https://introl.com/blog/vllm-production-deployment-inference-serving-architecture) | blog
-->

### When to Use It

**High-concurrency chat or API serving:** When you need to serve hundreds or thousands of concurrent users with an LLM-powered chatbot or API. vLLM's continuous batching and PagedAttention mean your GPUs stay fully utilized even under bursty traffic. If your workload involves 50+ concurrent requests, vLLM will significantly outperform naive serving approaches.

**Multi-turn conversation systems:** When users engage in multi-turn chat where every message resends the conversation history. Prefix caching avoids recomputing the shared history, reducing time-to-first-token dramatically as conversations grow longer.

**Document Q&A and RAG pipelines:** When the same documents are queried repeatedly by different users. Prefix caching ensures the document's KV cache is computed once and reused across all questions, turning expensive prefill operations into near-instant cache hits.

**Batch inference over large datasets:** When processing millions of prompts offline (evaluation, data annotation, synthetic data generation). vLLM's throughput optimization means you can process more prompts per GPU-hour, directly reducing compute costs.

**Self-hosted alternative to proprietary APIs:** When you need OpenAI API compatibility but with data privacy, cost control, or regulatory compliance requirements. vLLM's OpenAI-compatible server means zero client-side code changes.

### When NOT to Use It

**Single-user local inference:** If you're running a model on your laptop for personal use, Ollama or llama.cpp provides a simpler experience. vLLM is optimized for multi-user serving, not single-user interaction.

**Edge or mobile deployment:** vLLM requires CUDA-capable GPUs. For CPU-only, mobile, or embedded deployments, look at llama.cpp, ONNX Runtime, or MLC LLM.

**Models smaller than 1B parameters:** For very small models, the overhead of vLLM's scheduling and memory management may not provide meaningful benefits over simpler serving approaches.

**Workloads dominated by very short prompts and responses (< 50 tokens):** When both input and output are very short, the scheduling overhead per request becomes a larger fraction of total latency. Direct model inference or simpler frameworks may have lower per-request overhead.

**When you need fine-grained per-request GPU isolation:** vLLM batches multiple requests onto the same GPU for throughput. If you need strict isolation between requests (e.g., for security or billing purposes), you'll need a different approach.

### Real-World Examples

**Roblox -- AI Assistant at scale:** Roblox uses vLLM to power its AI Assistant feature, processing over 1 billion tokens per week. The platform serves millions of concurrent users, and vLLM's efficient batching keeps inference costs manageable at this scale.

**Stripe -- Cost reduction through migration:** Stripe migrated its LLM inference to vLLM and achieved a 73% reduction in inference costs, handling 50 million daily API calls on one-third of its previous GPU fleet. The combination of PagedAttention's memory efficiency and continuous batching's throughput optimization directly translated to GPU savings.

**IBM -- Enterprise AI platform:** IBM integrates vLLM into its watsonx AI platform for enterprise LLM serving, leveraging its support for multiple model architectures and quantization methods to serve diverse enterprise workloads on shared GPU infrastructure.

**Meta -- Internal LLM serving:** Meta uses vLLM for internal LLM serving workloads, contributing back to the project as a key maintainer. The project's governance moved under the Linux Foundation in 2024, reflecting its importance to the broader AI infrastructure ecosystem.

**Mistral AI -- Model serving infrastructure:** Mistral AI uses vLLM as part of its inference infrastructure for serving its model family, benefiting from the engine's support for the Mistral model architecture and its efficient handling of long-context workloads.
