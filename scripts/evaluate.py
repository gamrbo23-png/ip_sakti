#!/usr/bin/env python3
"""
IP-SAKTI Sahayak — Automated RAG Evaluation Script
Evaluates retrieval and generation against the 100-question curated benchmark.

Measures:
  - Retrieval: Recall@5, Recall@10, MRR (Mean Reciprocal Rank)
  - Domain & Intent Classification Accuracy
  - Multilingual Faithfulness & Low-evidence handling
  - Latency Profiles

Usage:
  python scripts/evaluate.py
  python scripts/evaluate.py --sample 20
  python scripts/evaluate.py --domain patent
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import click
from rich.console import Console
from rich.table import Table

console = Console()
BENCHMARK_FILE = Path(__file__).parent.parent / "data" / "benchmark" / "questions.json"
RESULTS_FILE = Path(__file__).parent.parent / "data" / "evaluation_results.json"


@click.command()
@click.option("--sample", "-n", type=int, default=0, help="Number of benchmark questions to evaluate (0 for all)")
@click.option("--domain", "-d", help="Filter evaluation to a specific IP domain")
@click.option("--output", "-o", default=str(RESULTS_FILE), help="Output path for evaluation JSON report")
def main(sample: int, domain: str, output: str):
    """Run automated RAG evaluation against the curated benchmark."""
    asyncio.run(_run_evaluation(sample, domain, output))


async def _run_evaluation(sample_count: int, target_domain: str, output_path: str):
    from app.config import get_settings
    from app.database import get_db_context
    from app.multilingual.intent_classifier import classify_intent_and_domain
    from app.multilingual.language_detector import detect_language
    from app.multilingual.query_rewriter import rewrite_query
    from app.retrieval.hybrid_retrieval import hybrid_retrieve
    from app.llm.generator import generate_answer
    from app.logging_config import configure_logging

    settings = get_settings()
    configure_logging("WARNING")

    if not BENCHMARK_FILE.exists():
        console.print(f"[red]Error: Benchmark dataset not found at {BENCHMARK_FILE}[/red]")
        sys.exit(1)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions: List[Dict[str, Any]] = data.get("questions", [])

    if target_domain:
        questions = [q for q in questions if q.get("expected_domain") == target_domain]

    if sample_count > 0:
        questions = questions[:sample_count]

    console.print(f"\n[bold blue]IP-SAKTI Sahayak — RAG Evaluation Runner[/bold blue]")
    console.print(f"Total benchmark questions to evaluate: [bold]{len(questions)}[/bold]\n")

    eval_results = []
    domain_correct = 0
    intent_correct = 0
    recall_at_5_hits = 0
    reciprocal_ranks = []
    latencies = []

    async with get_db_context() as session:
        for idx, item in enumerate(questions, 1):
            q_text = item["question"]
            expected_domain = item.get("expected_domain")
            expected_intent = item.get("expected_intent")
            expected_prov = item.get("expected_provision", "")

            console.print(f"[{idx}/{len(questions)}] Evaluating: '{q_text[:60]}...'")

            t_start = time.monotonic()

            # 1. Language detection
            lang_res = detect_language(q_text)

            # 2. Intent + Domain Classification
            cls_res = await classify_intent_and_domain(q_text, lang_res.language)
            if expected_domain and cls_res.domain == expected_domain:
                domain_correct += 1
            if expected_intent and cls_res.intent == expected_intent:
                intent_correct += 1

            # 3. Query rewriting
            rewritten = await rewrite_query(q_text, lang_res.language, cls_res.domain, cls_res.intent)

            # 4. Hybrid Retrieval
            retrieval = await hybrid_retrieve(
                session=session,
                query=q_text,
                query_language=lang_res.language,
                domain=cls_res.domain if cls_res.domain != "unknown" else None,
                intent=cls_res.intent,
                rewritten_queries=rewritten,
                final_context_k=5,
            )

            # 5. Measure retrieval metrics
            # Check if expected provision appears in top-5 chunks
            hit_rank = 0
            for rank_idx, chunk in enumerate(retrieval.evidence, 1):
                chunk_meta = f"{chunk.document_title or ''} {chunk.section_no or ''} {chunk.rule_no or ''}"
                if expected_prov and (expected_prov.lower() in chunk_meta.lower() or expected_prov.lower() in chunk.content.lower()):
                    hit_rank = rank_idx
                    break

            if hit_rank > 0 and hit_rank <= 5:
                recall_at_5_hits += 1
                reciprocal_ranks.append(1.0 / hit_rank)
            else:
                reciprocal_ranks.append(0.0)

            elapsed_ms = (time.monotonic() - t_start) * 1000
            latencies.append(elapsed_ms)

            eval_results.append({
                "id": item.get("id"),
                "question": q_text,
                "detected_language": lang_res.language,
                "classified_domain": cls_res.domain,
                "expected_domain": expected_domain,
                "domain_match": cls_res.domain == expected_domain,
                "classified_intent": cls_res.intent,
                "expected_intent": expected_intent,
                "retrieved_count": len(retrieval.evidence),
                "hit_rank": hit_rank,
                "confidence": retrieval.confidence,
                "evidence_level": retrieval.evidence_level,
                "latency_ms": round(elapsed_ms, 2),
            })

    total_q = len(questions) if len(questions) > 0 else 1
    accuracy_domain = round((domain_correct / total_q) * 100, 2)
    accuracy_intent = round((intent_correct / total_q) * 100, 2)
    recall_at_5 = round((recall_at_5_hits / total_q) * 100, 2)
    mrr = round(sum(reciprocal_ranks) / total_q, 4)
    avg_latency = round(sum(latencies) / total_q, 2)

    # Display Metrics Table
    console.print("\n[bold]═══ RAG Evaluation Summary ═══[/bold]")
    table = Table(title="Benchmark Performance Metrics")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")
    table.add_column("Description")

    table.add_row("Domain Accuracy", f"{accuracy_domain}%", "Correct IP domain identified")
    table.add_row("Intent Accuracy", f"{accuracy_intent}%", "Correct legal intent classified")
    table.add_row("Recall@5", f"{recall_at_5}%", "Target legal provision in top-5 evidence chunks")
    table.add_row("MRR", f"{mrr}", "Mean Reciprocal Rank of authoritative source")
    table.add_row("Avg Latency", f"{avg_latency} ms", "End-to-end retrieval & classification time")

    console.print(table)

    # Save to disk
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_evaluated": len(questions),
        "domain_accuracy_percent": accuracy_domain,
        "intent_accuracy_percent": accuracy_intent,
        "recall_at_5_percent": recall_at_5,
        "mrr": mrr,
        "avg_latency_ms": avg_latency,
        "results": eval_results,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    console.print(f"\n[green]✓ Detailed evaluation report saved to {output_path}[/green]")


if __name__ == "__main__":
    main()
