# IP-SAKTI Sahayak — Document Ingestion Pipeline Specification

## Ingestion Architecture

```
Official Source (IP India / Regulators)
          │
          ▼
Downloader (Async HTTP with Exponential Backoff)
          │
          ▼
SHA-256 Hash Calculation & Idempotency Check
          │
          ▼
PDF Text Extraction (PyMuPDF) + OCR Fallback (Tesseract)
          │
          ▼
Text Normalization & Noise Cleaning
          │
          ▼
Legal Structure Parser (Chapters, Sections, Rules, Forms)
          │
          ▼
Section-Aware Chunking (500–1200 tokens + Metadata Binding)
          │
          ▼
Dense Vector Generation (BGE-M3 1024-dim)
          │
          ▼
PostgreSQL Insertion + pgvector HNSW Indexing
```

---

## Idempotency & Versioning

1. **Content Hash Check**: Before parsing or chunking, the document's SHA-256 hash is computed. If unchanged in the database, ingestion is skipped.
2. **Version Control**: When an official document changes (e.g., an amendment to the Trade Marks Rules):
   - The prior version is updated to `status = 'SUPERSEDED'`.
   - The new version is inserted as `status = 'CURRENT'`.
   - Both versions remain searchable, but the retrieval engine prioritizes `CURRENT` unless historical context is explicitly requested.

---

## CLI Ingestion Commands

```bash
# Ingest all registered Indian IP sources
python scripts/ingest.py

# Ingest specific domain
python scripts/ingest.py --domain patent

# Force re-ingestion & re-embedding
python scripts/ingest.py --refresh

# Dry-run validation
python scripts/ingest.py --dry-run
```
