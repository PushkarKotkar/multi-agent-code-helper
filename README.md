# Multi-Agent Code Helper

## 1. Project Description
The Multi-Agent Code Helper is an intelligent pair-programming assistant built using the Google Agent Development Kit (ADK), LiteLLM with NVIDIA NIM, and Pinecone serverless vector search. It orchestrates a routing coordinator and four specialized worker agents to assist software developers in exploring, navigating, understanding, and onboarding onto codebases without hallucinating source code. By combining deterministic static AST analysis, custom RAG semantic search, and secure file inspection through a Model Context Protocol (MCP) server, it delivers accurate, evidence-backed answers to complex codebase queries.

---

## 2. Agents Table

| Agent Name | Role | Primary Responsibility | Backing Model & Framework |
| :--- | :--- | :--- | :--- |
| **`coordinator`** | Boss / Router | Evaluates user prompts and delegates them to the appropriate specialist worker. Never answers queries directly. | Google ADK `LlmAgent` + LiteLLM (`meta/llama-3.2-11b-vision-instruct`) |
| **`code_searcher`** | Specialist Worker | Locates where functions, settings, and features are implemented across the indexed repository using RAG vector similarity search. | Google ADK `LlmAgent` + LiteLLM |
| **`code_explainer`** | Specialist Worker | Reads and explains specific source files in detail, detailing architecture, function contracts, and dependencies without hallucinating unread code. | Google ADK `LlmAgent` + LiteLLM |
| **`architecture_mapper`** | Specialist Worker | Inspects Python modules, function signatures, class hierarchies, and import dependencies statically using Python AST. | Google ADK `LlmAgent` + LiteLLM |
| **`onboarding_guide`** | Specialist Worker | Guides new developers through the project layout, configuration, entry points, and sensible first steps. | Google ADK `LlmAgent` + LiteLLM |

---

## 3. Tools Table

| Tool Name | Origin / Module | Purpose |
| :--- | :--- | :--- |
| **`rag_search`** | `code_helper.tools.rag_tools` | Queries Pinecone with 2048-dimensional NVIDIA Nemotron embeddings to retrieve top-$k$ relevant code passages and source metadata. |
| **`read_file`** | `@modelcontextprotocol/server-filesystem` | MCP tool that securely reads actual source file content directly from disk for the `code_explainer`. |
| **`list_directory`** | `@modelcontextprotocol/server-filesystem` | MCP tool that lists files and subdirectories within the target repository path for file verification. |
| **`inspect_python_structure`** | `code_helper.tools.project_tools` | Parses target Python files using Python's built-in `ast` module to extract classes, functions, and imports safely without executing code. |
| **`list_project_files`** | `code_helper.tools.project_tools` | Recursively enumerates files in the configured project root using plain Python, ignoring `.git` and virtual environments. |
| **`get_onboarding_overview`** | `code_helper.tools.project_tools` | Inspects top-level project files and identifies entry points (`main.py`, `indexer.py`, etc.) for developer onboarding. |
| **`find_text_in_codebase`** | `code_helper.tools.project_tools` | Performs fast, deterministic substring searches across codebase files for exact variable names, constants, or strings. |

---

## 4. Chunk Size and Explanation

* **Selected Chunk Size:** `700` characters  
* **Selected Chunk Overlap:** `120` characters  

### Explanation:
Python source code is inherently structured around functions, class headers, docstrings, and control blocks that typically span between 500 and 800 characters. A chunk size of `700` characters is optimal because:
1. **Semantic Completeness:** It captures complete function declarations, signatures, and docstrings in a single chunk rather than slicing logical blocks mid-statement.
2. **Dense Vector Representation:** Overly large chunks (e.g., >2,000 characters) dilute semantic specificity when embedded by `nvidia/nemotron-3-embed-1b`, reducing cosine similarity scores during retrieval.
3. **Boundary Safety:** The `120`-character overlap—combined with our word-boundary and newline-boundary fallback algorithm—guarantees that statements, imports, and definitions crossing chunk borders are never cut in half or omitted from index coverage.

---

## 5. Model Context Protocol (MCP) Server

* **Server Used:** `@modelcontextprotocol/server-filesystem` (launched via `npx -y`)
* **Agent Utilizing MCP:** `code_explainer`

### Why This Server Was Used:
Large Language Models frequently hallucinate details when attempting to explain entire source files solely from fragmented vector chunks. By integrating the official **Filesystem MCP Server** over `stdio`, the `code_explainer` agent receives sandboxed, read-only access to the ground-truth codebase on disk. This enables the agent to call `read_file` and examine whole source files exactly as written, verifying function arguments, edge cases, and line numbers before generating explanations.

---

## 6. Exact Commands to Run

### Step 1: Environment Setup
Ensure Python 3.10+ and Node.js (with `npx`) are installed.

```powershell
# 1. Clone the target codebase to inspect (if not already cloned)
git clone https://github.com/voidgremlin19/Naive_RAG.git C:\Users\tejas\OneDrive\Desktop\data\Naive_RAG

# 2. In the Multi_Agent_Code_Helper root directory, install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy [.env.example](file:///.env.example) to `.env` and fill in your API keys:
```powershell
Copy-Item .env.example .env
```
Ensure your `.env` contains:
```ini
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_NIM_API_KEY=your_nvidia_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=code-helper
CODEBASE_PATH=C:/Users/tejas/OneDrive/Desktop/data/Naive_RAG
CHUNK_SIZE=700
CHUNK_OVERLAP=120
TOP_K=4
```

### Step 3: Run Automated Verification Tests
```powershell
python -m pytest tests/
```

### Step 4: Index the Target Codebase into Pinecone
```powershell
python -m code_helper.index_codebase
```

### Step 5: Launch the Multi-Agent System

#### Option A: Web Interface (Recommended)
```powershell
$env:PATH += ";$env:APPDATA\Python\Python314\Scripts"
adk web code_helper
```
Open **http://127.0.0.1:8000** in your browser.

#### Option B: Terminal Interactive Mode
```powershell
$env:PATH += ";$env:APPDATA\Python\Python314\Scripts"
adk run code_helper
```

---

## 7. Three Sample Questions and Answers

### Sample 1
* **User Question:** *"I am a new developer on this project, where should I start?"*
* **Answering Agent:** `onboarding_guide`
* **Agent Answer:**
  > Welcome to the project! The target repository (`Naive_RAG`) implements a Retrieval-Augmented Generation pipeline using NVIDIA NIM and Pinecone. Here is your ordered starting path:
  > 1. Read `Day4_Naive_RAG_Project_Build_Spec.md` for the high-level architecture and RAG specifications.
  > 2. Inspect `config.py` to understand how `RAGConfig` loads NVIDIA NIM endpoints and Pinecone settings.
  > 3. Review `vector_store.py` to see index creation and Pinecone serverless initialization.
  > 4. Trace `indexer.py` (ingestion stages: load, chunk, embed, store).
  > 5. Review `query_pipeline.py` and run `main.py` for the interactive query CLI.

---

### Sample 2
* **User Question:** *"Where is the vector database client initialized in this project?"*
* **Answering Agent:** `code_searcher`
* **Agent Answer:**
  > The vector database client is initialized in `vector_store.py`. Specifically:
  > - `get_pinecone_client(api_key)` instantiates the `Pinecone(api_key=api_key)` client.
  > - `ensure_pinecone_index_exists()` checks if the index exists and creates a serverless Pinecone index with dimension 2048 and cosine metric if not present.
  > - If no Pinecone key is configured, `vector_store.py` provides a deterministic fallback to `data/local_vector_db.json`.

---

### Sample 3
* **User Question:** *"Explain the functions and purpose of indexer.py."*
* **Answering Agent:** `code_explainer`
* **Agent Answer:**
  > `indexer.py` implements the four-stage ingestion pipeline for the Naive RAG system:
  > 1. `load_document(path)`: Reads raw text files from disk using UTF-8 encoding.
  > 2. `chunk_document(text, chunk_size, chunk_overlap)`: Splits text into overlapping chunks, prioritizing line boundaries.
  > 3. `embed_chunks(client, chunks)`: Sends batches of text to the NVIDIA NIM embedding API (`nvidia/nemotron-3-embed-1b`) and returns 2048-dimensional vectors.
  > 4. `store_in_vector_db(vectors, chunks, source, index)`: Upserts vector records along with metadata (`source`, `chunk`, `text`) into Pinecone.
  > 5. `run_indexing_pipeline()`: Orchestrates the stages across all document sources in the `data/` folder.

---

## 8. One Problem and Its Solution

### Problem:
During Phase 3 integration of the `code_explainer` agent with the Google Agent Development Kit (ADK), passing `tools=filesystem_tools` (where `filesystem_tools` was instantiated directly as `McpToolset(...)`) caused an immediate crash during agent initialization with:
```text
TypeError: 'McpToolset' object is not iterable
```
Additionally, during unit testing of document chunking, single-line text without newline characters caused `chunk_document` to slice words mid-character across chunk boundaries (e.g., splitting `"delta"` into `"delt"` in one chunk and `"elta"` in the next), resulting in `AssertionError: assert 'delta' in ...`.

### Solution:
1. **ADK McpToolset Packaging:** Google ADK's `LlmAgent` validator expects the `tools` parameter to be an iterable sequence of tools and toolsets. We resolved the initialization failure by wrapping `McpToolset` inside a list: `filesystem_tools = [McpToolset(...)]`.
2. **Word-Boundary Chunker Fallback:** In `code_helper/index_codebase.py`, we enhanced `chunk_document` with a secondary search for space boundaries (`" "`) if no newline character (`"\n"`) is found within the chunk window. This guarantees words and identifiers remain intact across chunk boundaries, resolving the test failure and ensuring 100% test pass rates across the suite.
