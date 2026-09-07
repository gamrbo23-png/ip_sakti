# IP-SAKTI Sahayak — REST API Specification

Base URL: `http://localhost:8000` (FastAPI) | Interactive Docs: `http://localhost:8000/docs`

---

## Endpoints

### 1. Chat & Guidance
- **`POST /api/chat`**
  - **Body**:
    ```json
    {
      "query": "How do I register a trademark in India?",
      "session_id": "session_12345",
      "language": "en",
      "domain": "trademark",
      "include_trace": false
    }
    ```
  - **Response**:
    ```json
    {
      "session_id": "session_12345",
      "message_id": 1,
      "answer": "...",
      "language": "en",
      "domain": "trademark",
      "intent": "registration",
      "confidence": 0.92,
      "evidence_level": "high",
      "citations": [
        {
          "citation_number": 1,
          "document_title": "Trade Marks Rules, 2017",
          "section_no": null,
          "rule_no": "23",
          "authority": "IP India / CGPDTM",
          "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOAct/1_107_1_TM_Rules_2017.pdf",
          "status": "CURRENT",
          "is_current": true
        }
      ],
      "evidence": [...],
      "retrieval_trace_id": "uuid-here",
      "has_sufficient_evidence": true
    }
    ```

- **`GET /api/chat/{session_id}`**
  - Retrieves chronological conversation history for a given session.

### 2. Search & Knowledge Exploration
- **`POST /api/search`**: Full-text and vector search over indexed chunks.
- **`GET /api/sources`**: Returns active official Indian IP knowledge sources.
- **`GET /api/domains`**: Returns supported domain taxonomy.
- **`GET /api/laws`**: Lists indexed Acts, Rules, Manuals, and Gazette documents.

### 3. User Feedback & Document Analysis
- **`POST /api/feedback`**: Submit helpful (+1) or not helpful (-1) rating.
- **`POST /api/documents/upload`**: Upload PDF/TXT for statutory cross-referencing.

### 4. Admin & Health
- **`GET /api/admin/stats`**: Aggregated corpus, latency, and feedback statistics.
- **`POST /api/admin/ingest`**: Trigger async ingestion pipeline.
- **`GET /health`**: Liveness check.
- **`GET /ready`**: Readiness check verifying PostgreSQL, pgvector, and embedding models.
