# Project implementation notes (README to be added after user supplies format)

This deliverable adapts the `voidgremlin19/Naive_RAG` repository's NVIDIA NIM + Pinecone approach to the separate Multi-Agent Code Helper assignment in the Student Guide.

- The original Naive RAG project provides the baseline concepts: NVIDIA NIM embeddings, Pinecone serverless vectors, chunking, and retrieval.
- This project adds Google ADK orchestration and four specialist workers under a routing-only coordinator.
- Pinecone index dimension is set to 2048 and metric to cosine, matching the source repository's embedding model guidance.
- `CODEBASE_PATH` should point to the cloned `Naive_RAG` folder to have the helper inspect that repository. The helper folder and target codebase should not be the same folder if you want the agent to analyse Naive_RAG rather than itself.
- The required README.md is intentionally deferred until the user provides the requested README format.
