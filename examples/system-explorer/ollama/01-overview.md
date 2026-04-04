## Overview
<!-- level: beginner -->
<!-- references:
- [Ollama Official Website](https://ollama.com/) | official-docs
- [Ollama GitHub Repository](https://github.com/ollama/ollama) | github
- [Ollama Documentation](https://docs.ollama.com/) | official-docs
-->

Ollama is a local LLM inference runtime that makes running large language models on your own machine as simple as running a Docker container. It wraps the complexity of model quantization, GPU memory management, and inference backends behind a single CLI command and REST API. With Ollama, you can download and run models like Llama, Gemma, Qwen, and DeepSeek with one command: `ollama run llama3.2`.

The project has grown rapidly since its initial release, becoming the de facto standard for local LLM inference among developers. It supports macOS, Linux, and Windows, with automatic GPU acceleration on NVIDIA (CUDA), AMD (ROCm), and Apple Silicon (Metal/MLX). As of v0.20.0, Ollama supports multimodal models, tool calling, structured outputs, web search capabilities, and an [OpenAI-compatible API](https://docs.ollama.com/api/) that makes it a drop-in replacement for cloud LLM APIs in development workflows.

### What It Is

Ollama is a local LLM runtime -- like a personal Docker for AI models. Just as Docker lets you pull and run containerized applications without worrying about dependencies, Ollama lets you pull and run language models without worrying about model formats, quantization levels, GPU drivers, or inference engine configuration. You say `ollama run`, and it handles everything.

### Who It's For

Ollama is built for developers who want to integrate LLMs into their applications without sending data to cloud APIs. It serves AI engineers prototyping with local models, backend developers building LLM-powered features, privacy-conscious teams that need data to stay on-premises, and hobbyists experimenting with open-source models on consumer hardware. If you have a Mac with 16GB+ RAM or a PC with an NVIDIA GPU, Ollama can run meaningful models for you.

### The One-Sentence Pitch

Ollama is the simplest way to run open-source LLMs locally -- one command to download, one command to run, with a REST API that works like OpenAI's.
