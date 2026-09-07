# IP-SAKTI Sahayak — Evaluation & Benchmark Specification

## Evaluation Framework

IP-SAKTI Sahayak includes a manually curated benchmark dataset (`data/benchmark/questions.json`) comprising **100 realistic legal and regulatory questions** across all supported Indian IP domains:
- **Patents (20 questions)**
- **Trade Marks (20 questions)**
- **Copyright (20 questions)**
- **Industrial Designs (15 questions)**
- **Geographical Indications (10 questions)**
- **Startup & Regulatory Compliance (15 questions)**

Languages covered: **English, Hindi, Bengali, Tamil, Telugu, and Hinglish / mixed-language queries**.

---

## Evaluation Metrics

1. **Recall@5 & Recall@10**: Percentage of queries where the target statutory provision / rule appears in the top-5 or top-10 retrieved candidate chunks.
2. **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant official source passage.
3. **Classification Accuracy**: Percentage of queries where domain and intent are accurately identified.
4. **Faithfulness / Groundedness**: Verification that all returned claims map to retrieved evidence chunks without unsupported assertions.
5. **Latency**: End-to-end processing time for retrieval, reranking, and generation.

---

## Running the Benchmark

```bash
# Run full 100-question evaluation
python scripts/evaluate.py

# Run on a sample of 20 questions
python scripts/evaluate.py --sample 20

# Run on a single domain
python scripts/evaluate.py --domain trademark
```

Results are printed in a rich terminal summary table and saved as JSON to `data/evaluation_results.json` for presentation.
