# IP-SAKTI Sahayak — RAG & Multilingual Retrieval Specification

## 1. Multilingual Natural Language Understanding (NLU)

### Language Detection
Input queries are analyzed across Unicode scripts (Devanagari, Bengali, Tamil, Telugu, Latin) combined with a Hinglish transliteration keyword vocabulary and `langdetect` fallback:
- **Hindi (`hi`)**: Devanagari script queries.
- **Bengali (`bn`)**: Bengali script queries.
- **Tamil (`ta`)**: Tamil script queries.
- **Telugu (`te`)**: Telugu script queries.
- **Hinglish (`mixed`)**: Code-switched Latin/Devanagari queries (e.g. *"Mere brand name ko trademark kaise protect karein?"*).

### Intent and Domain Classification
Every query is categorized into:
- **IP Domains**: `patent`, `trademark`, `copyright`, `design`, `gi`, `sicld`, `startup`, `data_protection`, `regulatory_general`.
- **Intents**: `definition`, `eligibility`, `registration`, `procedure`, `documents`, `fees`, `timeline`, `renewal`, `opposition`, `infringement`, `ownership`, `licensing`, `assignment`, `compliance`, `comparison`, `source_lookup`, `amendment_lookup`, `general_ip_guidance`.

### Cross-Lingual Query Expansion
Because the primary statutory corpus is in English and official gazette formats, cross-lingual queries (e.g., in Hindi or Bengali) are expanded into 3–5 targeted English retrieval search queries while preserving the user's intent.

---

## 2. Hybrid Retrieval Pipeline

### Step 1: Dense Vector Search (pgvector)
- **Model**: `BAAI/BGE-M3` (1024-dimensional normalized dense vectors).
- **Index**: PostgreSQL HNSW cosine index:
  ```sql
  SELECT c.id, c.content, c.document_title, c.section_no, c.rule_no,
         1 - (c.embedding <=> :query_vec::vector) AS similarity_score
  FROM chunks c
  WHERE c.status = 'CURRENT'
  ORDER BY c.embedding <=> :query_vec::vector
  LIMIT :limit;
  ```

### Step 2: Full-Text Keyword & Exact Provision Search
- Queries are scanned for explicit citations (e.g. *"Section 18"*, *"Rule 23"*). Exact matches are fetched immediately.
- General terms are searched via PostgreSQL `ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', :query))`.

### Step 3: Reciprocal Rank Fusion (RRF)
Vector candidates ($V$) and keyword candidates ($K$) are unified via:
$$RRF(d) = \sum_{m \in \{V, K\}} \frac{1}{60 + \text{rank}_m(d)}$$

### Step 4: Cross-Encoder Reranking
Top candidates are reranked using `BAAI/bge-reranker-v2-m3` for fine-grained relevance scoring.

---

## 3. Hallucination Control & Confidence Tiers

1. **High Evidence ($\ge 0.75$)**: Normal grounded explanation with full citations.
2. **Moderate Evidence ($0.45 - 0.74$)**: Grounded explanation with cautionary notice.
3. **Limited Evidence ($< 0.45$)**: Automatic refusal to hallucinate; provides direct links to the official IP India / regulator portal.
