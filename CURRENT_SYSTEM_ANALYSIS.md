# IP-SAKTI Sahayak — Current System Analysis

This document provides a complete, clear, and beginner-friendly breakdown of how the **IP-SAKTI Sahayak** backend and Retrieval-Augmented Generation (RAG) system currently work.

---

## 1. Complete Backend Folder Structure

The backend is organized cleanly into modular folders under [`backend/`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/):

```
backend/
├── app/
│   ├── main.py                     # Entry point for the FastAPI web server
│   ├── config.py                   # Reads environment variables (.env) and configuration
│   ├── database.py                 # Connects to SQLite / PostgreSQL using SQLAlchemy
│   ├── logging_config.py           # Configures clean, structured console logs
│   │
│   ├── api/                        # REST API routes (Endpoints that the frontend calls)
│   │   ├── chat.py                 # Chat & conversation history endpoints (/api/chat)
│   │   ├── endpoints.py            # Sources, search, laws, feedback, upload, and admin APIs
│   │   ├── health.py               # Health & readiness check endpoints (/health, /ready)
│   │   ├── admin.py                # Re-exports admin router
│   │   ├── documents.py            # Re-exports document upload router
│   │   ├── feedback.py             # Re-exports user feedback router
│   │   ├── search.py               # Re-exports search router
│   │   └── sources.py              # Re-exports sources and laws router
│   │
│   ├── models/
│   │   └── models.py               # 13 Database table definitions (SQLAlchemy ORM)
│   │
│   ├── schemas/
│   │   └── schemas.py              # Pydantic models (defines what request/response JSON looks like)
│   │
│   ├── multilingual/               # Language & intent understanding
│   │   ├── language_detector.py    # Detects Hindi, Bengali, Tamil, Telugu, English, Hinglish
│   │   ├── intent_classifier.py    # Figures out what domain (e.g. Patent) and intent (e.g. Fees)
│   │   └── query_rewriter.py       # Converts Indian language queries into English search queries
│   │
│   ├── retrieval/                  # The search engines that find relevant legal sections
│   │   ├── hybrid_retrieval.py     # Merges vector search and keyword search together (RRF)
│   │   ├── vector_retrieval.py     # Semantic similarity search using mathematical vectors
│   │   └── keyword_retrieval.py    # Exact section/rule number & full-text keyword search
│   │
│   ├── services/                   # AI services for embedding and reranking
│   │   ├── embedding_service.py    # Converts text into numbers (vectors) using BGE-M3
│   │   └── reranker_service.py     # Scores retrieved text passages using BGE-Reranker
│   │
│   ├── ingestion/                  # How legal documents are processed and saved
│   │   ├── pipeline.py             # Master step-by-step document ingestion pipeline
│   │   ├── chunker.py              # Splits long legal text into small, clean sections
│   │   ├── legal_parser.py         # Detects Chapters, Sections, Rules, Schedules using regex
│   │   ├── pdf_extractor.py        # Reads text from PDF files (with OCR fallback)
│   │   ├── downloader.py           # Downloads official PDF documents from government URLs
│   │   └── source_registry.py      # Loads the list of official government sources
│   │
│   └── llm/
│       └── generator.py            # Prepares prompts, talks to Gemini/LLM, and builds citations
│
├── alembic/                        # Database migration scripts
├── sql/
│   └── init.sql                    # SQL script to initialize PostgreSQL extensions (pgvector, pg_trgm)
├── tests/                          # Automated unit and integration tests
│   ├── test_api.py                 # Tests for API endpoints
│   ├── test_chunker.py             # Tests for chunking and section extraction
│   └── test_multilingual.py        # Tests for language detection and intent classification
└── Dockerfile                      # Container definition for the backend
```

---

## 2. Entry Point of the FastAPI Application

* **File Path**: [`backend/app/main.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/main.py)

### How it works:
1. **Application Startup (`lifespan`)**:
   - When the server starts up, it runs the `lifespan` function (lines 26–46).
   - It calls `init_extensions()` in [`backend/app/database.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/database.py) to make sure database tables are created.
   - It loads the embedding model into memory so it is ready for queries.
2. **Middleware**:
   - **CORS (`CORSMiddleware`)**: Allows the Next.js frontend running on `http://localhost:3000` to talk to the backend on `http://localhost:8000`.
   - **Timing (`add_request_timing`)**: Measures how many milliseconds each request takes and attaches an `X-Process-Time` header.
   - **Logging (`log_requests`)**: Prints clean log messages for every incoming request and response.
3. **Routers**:
   - It connects all endpoint routers (`health`, `chat`, `search`, `sources`, `feedback`, `documents`, `admin`) to the FastAPI app (lines 120–128).

---

## 3. Database Being Used and Connection Configuration

* **Active Database**: **SQLite** (a lightweight local file database named `ipsakti.db` in the project root).
* **Configuration File**: [`backend/app/config.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/config.py)
* **Connection Engine**: [`backend/app/database.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/database.py)
* **Active Environment Setting** ([`.env`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/.env)):
  ```env
  DATABASE_URL=sqlite+aiosqlite:///./ipsakti.db
  ```

### How the Database Connection Works:
- The system uses **SQLAlchemy AsyncEngine** (`create_async_engine`).
- When a user asks a question or makes an API call, FastAPI uses the `get_db` dependency ([`database.py:53`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/database.py#L53)) to provide a dedicated async database session (`AsyncSession`) and automatically commits or rolls back if an error occurs.
- **PostgreSQL Support**: The code is also fully prepared to connect to a PostgreSQL database with `pgvector` if you change `DATABASE_URL` in `.env` or run `docker-compose.yml`.

---

## 4. All Database Tables and Their Purpose

All 13 database tables are defined in [`backend/app/models/models.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/models/models.py):

| Table Name | Model Class | Purpose in Simple Words |
|---|---|---|
| `sources` | `Source` | Keeps a list of official government sources (e.g., IP India, Copyright Office) with URLs and authority tiers. |
| `documents` | `Document` | Stores information about each downloaded legal document (e.g., "The Patents Act, 1970", status, page count). |
| `document_versions` | `DocumentVersion` | Tracks version history and amendments of acts and rules over time. |
| `document_sections` | `DocumentSection` | Stores the high-level outline of documents (Chapters, Parts). |
| `chunks` | `Chunk` | **The most important table in RAG**. Stores small pieces of legal text (500–1200 tokens) with their exact section number, rule number, chapter, and mathematical embedding vector. |
| `legal_entities` | `LegalEntity` | Exact references to specific named legal sections and forms for fast direct lookups. |
| `chat_sessions` | `ChatSession` | Represents a single conversation thread with a user. |
| `chat_messages` | `ChatMessage` | Stores every message sent by the user and every response generated by the AI assistant. |
| `retrieval_logs` | `RetrievalLog` | Records debugging traces for every query: what queries were generated, how many chunks were found, latency, and confidence. |
| `feedback` | `Feedback` | Stores thumbs up (+1) / thumbs down (-1) ratings and comments submitted by users. |
| `users` | `User` | Stores registered users and admin credentials. |
| `ingestion_jobs` | `IngestionJob` | Tracks background document download and indexing jobs. |
| `system_events` | `SystemEvent` | Audit log for system errors and events. |

---

## 5. Does the Database Currently Contain Data?

We inspected the actual `ipsakti.db` SQLite database file:

* **Sources (`sources`)**: **0 rows**
* **Documents (`documents`)**: **0 rows**
* **Legal Chunks (`chunks`)**: **0 rows**
* **Chat Sessions (`chat_sessions`)**: **13 rows** (saved from previous tests)
* **Chat Messages (`chat_messages`)**: **30 rows** (saved from previous tests)
* **Retrieval Logs (`retrieval_logs`)**: **15 rows**
* **Feedback (`feedback`)**: **1 row**

### Why this matters:
Because `sources`, `documents`, and `chunks` contain **0 rows**, the retrieval engine finds **no legal evidence** when a user asks a question. This is why the AI assistant currently returns the low-evidence fallback message:
> *"I could not find sufficient authoritative information in the current knowledge base to answer this reliably."*

---

## 6. Location and Working of `scripts/ingest.py`

* **File Path**: [`scripts/ingest.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/scripts/ingest.py)

### How it works:
`scripts/ingest.py` is the command-line script that loads documents into the knowledge base:
1. It reads the list of registered sources from `data/metadata/source_registry.json`.
2. It loops through each source and calls `ingest_source_entry()` from [`backend/app/ingestion/pipeline.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/ingestion/pipeline.py).
3. It downloads the PDF, extracts the text, identifies sections, creates chunks, computes embedding vectors, and saves them into the `chunks` database table.
4. It prints a progress table and summary report in your terminal.

---

## 7. Location and Structure of `source_registry.json`

* **File Path**: [`data/metadata/source_registry.json`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/data/metadata/source_registry.json)

### Structure:
It is a JSON file listing 17 official Indian government statutory sources. Each entry has:
```json
{
  "id": "src_patent_act_1970",
  "name": "The Patents Act, 1970",
  "authority": "IP India / CGPDTM",
  "authority_tier": "TIER_1",
  "domain": "patent",
  "document_type": "act",
  "url": "https://ipindia.gov.in/writereaddata/Portal/IPOGuide/1_38_1_patent-act-1970-11march2015.pdf",
  "alternate_urls": ["https://ipindia.gov.in/patents.htm"],
  "description": "The primary Indian legislation governing patents, as amended.",
  "language": "en",
  "status": "ACTIVE"
}
```

---

## 8. How Documents are Downloaded or Loaded

* **File Path**: [`backend/app/ingestion/downloader.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/ingestion/downloader.py)

### How it works:
1. Uses `aiohttp` to download the PDF from official government URLs (e.g., `ipindia.gov.in`, `copyright.gov.in`).
2. Calculates the **SHA-256 hash** of the downloaded file.
3. Checks if the file is already downloaded. If the hash has not changed, it skips redownloading (saving bandwidth and time).
4. Saves the raw file into `data/raw/<domain>/` with a clean name like `src_patent_act_1970_<hash>.pdf`.

---

## 9. How Text Extraction Works

* **File Path**: [`backend/app/ingestion/pdf_extractor.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/ingestion/pdf_extractor.py)

### How it works:
1. Uses **PyMuPDF (`fitz`)** to open the PDF file.
2. Iterates page by page and extracts the text using `page.get_text("text")`.
3. **Scanned Page Detection & OCR Fallback**: If a page contains fewer than 50 text characters (meaning it is a scanned image rather than digital text), it automatically renders the page at 300 DPI and runs **Tesseract OCR** (`pytesseract.image_to_string`).
4. **Text Cleaning**: Cleans up whitespace, removes null bytes, and normalizes line breaks.

---

## 10. How Chunking Works

* **File Paths**:
  - Structure Parser: [`backend/app/ingestion/legal_parser.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/ingestion/legal_parser.py)
  - Section Chunker: [`backend/app/ingestion/chunker.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/ingestion/chunker.py)

### How it works:
Standard AI splitters cut text blindly by character count, which breaks legal sections in half. IP-SAKTI uses a **Section-Aware Legal Chunker**:
1. `legal_parser.py` uses regular expressions (regex) to identify:
   - Chapters (`CHAPTER II`)
   - Sections (`Section 3. What are not inventions`)
   - Rules (`Rule 23`)
   - Forms (`FORM TM-1`)
   - Schedules (`FIRST SCHEDULE`)
2. `chunker.py` bundles these provisions into chunks of **500 to 1,200 tokens** (around 2,000 to 4,800 characters).
3. It adds a **100-token overlap** between chunks so context is never lost.
4. Every single chunk gets tagged with metadata: `section_no`, `rule_no`, `chapter`, `page_number`, `document_title`, `authority`, and `source_url`.

---

## 11. How Embeddings are Generated

* **File Path**: [`backend/app/services/embedding_service.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/services/embedding_service.py)

### How it works:
1. **Primary Model**: Configured to use **BAAI/BGE-M3** (`FlagEmbedding`), which creates a **1,024-dimensional dense vector** for each text passage.
2. **Normalization**: Vectors are normalized to unit length so that cosine similarity can be computed using simple dot products.
3. **Fallback Mode**: If `FlagEmbedding` or PyTorch is not installed in the local Python virtual environment, the code automatically activates `_fallback_vector()`. This uses SHA-256 hashing to generate a deterministic 1,024-dimensional vector so the system continues running without crashing.

---

## 12. Where Embeddings are Stored

* **File Path**: [`backend/app/models/models.py:256`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/models/models.py#L256)

### How it works:
- Embeddings are stored directly in the `chunks` database table inside the `embedding` column.
- **In PostgreSQL**: Stored as a native `vector(1024)` column type with an **HNSW index** for ultra-fast similarity search.
- **In SQLite**: Stored as a **JSON array** of 1,024 float numbers (`[0.023, -0.041, ...]`).

---

## 13. How Vector Search Works

* **File Path**: [`backend/app/retrieval/vector_retrieval.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/retrieval/vector_retrieval.py)

### How it works:
1. The user's query is converted into a 1,024-dimensional query vector.
2. **In PostgreSQL**: Executes SQL using the pgvector cosine distance operator `<=>`:
   ```sql
   SELECT id, content, 1 - (embedding <=> :query_vec::vector) AS similarity_score
   FROM chunks
   WHERE status = 'CURRENT'
   ORDER BY embedding <=> :query_vec::vector LIMIT 20;
   ```
3. **In SQLite Fallback**: Loads chunks and uses `numpy.dot(q_vec, chunk_vec)` in memory to calculate cosine similarity and sort the top 20 candidates.

---

## 14. How Keyword / Full-Text Search Works

* **File Path**: [`backend/app/retrieval/keyword_retrieval.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/retrieval/keyword_retrieval.py)

### How it works:
Keyword search ensures that specific legal terms or section numbers are never missed:
1. **Exact Section/Rule Match**: If the user writes *"Section 3"* or *"Rule 23"*, regex extracts `section_no="3"` and immediately fetches exact matching rows from the database.
2. **Full-Text Search (FTS)**:
   - **In PostgreSQL**: Uses `tsvector` with `ts_rank_cd` and `plainto_tsquery('english', query)`.
   - **In SQLite Fallback**: Checks word matches and token frequency using `LIKE`.

---

## 15. How Reciprocal Rank Fusion (RRF) Works

* **File Path**: [`backend/app/retrieval/hybrid_retrieval.py:50-85`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/retrieval/hybrid_retrieval.py#L50-L85)

### How it works:
Vector search is great at understanding general meaning, while Keyword search is great at finding exact words. **RRF unifies both results without needing complex weights**:
$$\text{RRF Score} = \sum \frac{1}{60 + \text{Rank}}$$
- If a chunk ranks #1 in Vector search and #1 in Keyword search, its score is:
  $$\frac{1}{60 + 1} + \frac{1}{60 + 1} = 0.01639 + 0.01639 = 0.03278$$
- If a chunk only appears in one list, its score is lower.
- The system sorts all unique chunks by their combined RRF score and passes the top candidates to the reranker.

---

## 16. How Reranking Works

* **File Path**: [`backend/app/services/reranker_service.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/services/reranker_service.py) & [`hybrid_retrieval.py:214-255`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/retrieval/hybrid_retrieval.py#L214-L255)

### How it works:
1. **Cross-Encoder Model**: The top candidate passages from RRF are sent to **`BAAI/bge-reranker-v2-m3`**.
2. Unlike vector search which compares embeddings separately, the reranker evaluates the user's question and candidate text passage together to compute a deep semantic relevance score (0.0 to 1.0).
3. **Statutory Authority Bonus**: Tier-1 government statutory sources (e.g. Acts and Rules) receive a $+0.1$ priority bonus over secondary summaries.
4. The top 5 highest-scoring evidence chunks are selected for the final LLM prompt.

---

## 17. Complete RAG Flow from Question to Answer

Here is the exact step-by-step journey of a question:

```
1. USER ENTERS QUESTION (e.g. "मैं अपने ब्रांड नाम को ट्रेडमार्क कैसे करूं?")
   │
   ▼
2. LANGUAGE DETECTION (backend/app/multilingual/language_detector.py)
   Detects script (Devanagari) -> Language identified as Hindi ('hi').
   │
   ▼
3. INTENT & DOMAIN CLASSIFICATION (backend/app/multilingual/intent_classifier.py)
   Identifies Domain: 'trademark' | Intent: 'registration'.
   │
   ▼
4. QUERY REWRITING (backend/app/multilingual/query_rewriter.py)
   Expands Hindi query into English legal search queries:
   ["trademark registration procedure", "Trade Marks Act 1999 registration"]
   │
   ▼
5. HYBRID RETRIEVAL (backend/app/retrieval/hybrid_retrieval.py)
   - Vector search finds semantically related chunks.
   - Keyword search finds matching provisions.
   - RRF merges results and BGE Reranker scores top passages.
   │
   ▼
6. EVIDENCE & CONFIDENCE CHECK
   - If 0 chunks found OR confidence < 0.45:
       -> Returns Low-Evidence Refusal Response (Abstention).
   - If chunks found AND confidence >= 0.45:
       -> Injects evidence into prompt and calls Gemini 1.5 Flash.
   │
   ▼
7. GROUNDED ANSWER & CITATION GENERATION (backend/app/llm/generator.py)
   LLM explains the answer in Hindi, but cites verified Section/Rule provisions.
   │
   ▼
8. SAVING & RETURNING
   - Saves message to `chat_messages` and trace to `retrieval_logs`.
   - Returns structured JSON with answer, citations, and evidence drawer to UI.
```

---

## 18. How Gemini or the LLM is Connected

* **File Path**: [`backend/app/llm/generator.py:253-275`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/llm/generator.py#L253-L275)

### How it works:
1. Google Gemini provides an **OpenAI-compatible API endpoint**.
2. The backend uses the official `openai.AsyncOpenAI` client initialized with:
   - `base_url`: `https://generativelanguage.googleapis.com/v1beta/openai/`
   - `api_key`: Loaded from `.env` (`OPENAI_API_KEY`)
   - `model`: `gemini-1.5-flash`
3. It sends a strict **System Prompt** instructing the model:
   - *Use ONLY the retrieved evidence.*
   - *Never invent laws, sections, fees, or deadlines.*
   - *Attach citations `[Citation X]` to every legal statement.*
   - *Respond in the user's language (e.g. Hindi/Bengali) while displaying English legal terms in brackets.*

---

## 19. How Citations are Generated

* **File Path**: [`backend/app/llm/generator.py:154-175`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/llm/generator.py#L154-L175)

### How it works:
1. Citations are **not invented by the LLM**.
2. The backend extracts `document_title`, `section_no`, `rule_no`, `chapter`, `page_number`, `authority`, and `source_url` directly from the database `Chunk` records retrieved during Step 5.
3. The LLM references them as `[Citation 1]`, `[Citation 2]`.
4. The backend packages these citations into structured `CitationResponse` objects which the Next.js frontend renders as clickable pills with direct links to the official government PDF!

---

## 20. How Evidence-Based Abstention Works

* **File Path**: [`backend/app/llm/generator.py:200-222`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/backend/app/llm/generator.py#L200-L222)

### How it works:
In legal matters, giving a hallucinated answer is dangerous. IP-SAKTI implements **Evidence-Based Abstention**:
1. If the retrieval engine finds **0 matching chunks**, or if the confidence score is below $0.45$:
2. The LLM is **not called** to guess an answer.
3. Instead, the backend immediately returns a safe refusal message:
   > *"I could not find sufficient authoritative information in the current knowledge base to reliably answer this question..."*
4. It provides direct links to the official [IP India](https://ipindia.gov.in) portal and reminds the user to consult an authorized attorney.

---

## 21. Which Features are Fully Working

- [x] **Next.js 14 Frontend UI**: Complete responsive interface, chat UI, dark/light theme, Markdown rendering, Text-to-Speech audio, and feedback buttons.
- [x] **FastAPI Backend Server**: All 14 API endpoints running and responding to requests.
- [x] **Gemini 1.5 Flash LLM Connection**: Real-time integration via OpenAI-compatible endpoint.
- [x] **Language Detection**: Automatically detects English, Hindi, Bengali, Tamil, Telugu, and Hinglish.
- [x] **Intent & Domain Classification**: Correctly classifies questions into domains (Patent, Trademark, etc.) and intents (Fees, Procedure, etc.).
- [x] **Query Rewriting**: Expands Indic language queries into English search terms.
- [x] **Section-Aware Chunking & Parsing**: `legal_parser.py` and `chunker.py` correctly split statutory text.
- [x] **PDF Text Extraction**: PyMuPDF (`fitz`) successfully reads text from PDF files.
- [x] **Evidence-Based Abstention**: Safely prevents hallucinations when evidence is missing.
- [x] **Document Upload Analyzer (`/upload`)**: Uploads PDF/TXT files and extracts text in memory.
- [x] **Database Session Logging**: Saves user chats, assistant answers, and retrieval trace latencies.

---

## 22. Which Features are Partially Implemented

- [~] **Knowledge Base Corpus**: The ingestion pipeline and database models are built, but the database currently contains **0 chunks** because the ingestion script has not been run.
- [~] **Embeddings & Reranking**: BGE-M3 and BGE-Reranker code is written, but running in fallback mode in the default local virtual environment.
- [~] **Document Ingestion (`scripts/ingest.py`)**: Script is written and ready, but awaiting execution to populate `ipsakti.db`.
- [~] **PostgreSQL & pgvector**: Configured in `docker-compose.yml` and `sql/init.sql`, but the local `.env` is currently pointing to SQLite.

---

## 23. Which Features are Placeholders or Fallbacks

| Feature | Where Found | Current Behavior | What it Should Become |
|---|---|---|---|
| **"What Protects My Idea?" Wizard** | `frontend/app/page.tsx:70` | Uses basic client-side JavaScript keyword matching (`lower.includes('software')`). | Should be a multi-turn backend statutory route-mapping agent. |
| **Embedding Fallback** | `backend/app/services/embedding_service.py:129` | Generates deterministic SHA-256 projection vectors when `FlagEmbedding` is absent. | Real local or API-driven dense vector embeddings. |
| **Reranker Fallback** | `backend/app/services/reranker_service.py:80` | Uses token overlap percentage when BGE cross-encoder is absent. | Full neural cross-encoder reranking. |
| **LLM Offline Fallback** | `backend/app/llm/generator.py:303` | Shows plain raw evidence snippets if the LLM API call fails. | Retry mechanism with backup LLM provider. |

---

## 24. Which Files Must Be Modified to Populate the Knowledge Base

To turn this prototype into a fully populated legal AI assistant:

1. **Add Domain Sources (Ayurveda & Bio-patentability)**:
   - File: [`data/metadata/source_registry.json`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/data/metadata/source_registry.json)
   - Add entries for:
     * *The Biological Diversity Act, 2002 & 2023 Amendments*
     * *TKDL (Traditional Knowledge Digital Library) Guidelines*
     * *Drugs and Cosmetics Act (Ayurvedic provisions)*

2. **Execute Ingestion**:
   - Run the script:
     ```powershell
     python scripts/ingest.py
     ```
   - This will download all official PDFs, chunk the legal text, generate embeddings, and populate the `chunks` table in `ipsakti.db`.

3. **Verify Evaluation Benchmark**:
   - File: [`scripts/evaluate.py`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/scripts/evaluate.py)
   - Run:
     ```powershell
     python scripts/evaluate.py
     ```
   - This tests Recall@5 and classification accuracy against the 100 benchmark questions in [`data/benchmark/questions.json`](file:///c:/Users/arghy/OneDrive/Documents/HACKATHIN%20PROJECT/HACKATHON%20PROJECT/ip-sakti/data/benchmark/questions.json).
