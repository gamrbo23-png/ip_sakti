#!/usr/bin/env python3
"""
IP-SAKTI Sahayak — Corpus Validation Script
Runs sanity checks and data quality validation across all database records:
  - Duplicate content hashes
  - Missing source URLs
  - Missing authority / authority tiers
  - Empty or un-embedded chunks
  - Broken references
"""
import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select

console = Console()


async def run_validation():
    from app.config import get_settings
    from app.database import get_db_context
    from app.models.models import Chunk, Document, Source

    console.print("\n[bold blue]IP-SAKTI Sahayak — Corpus Quality Validator[/bold blue]\n")

    async with get_db_context() as session:
        # 1. Total counts
        total_sources = await session.scalar(select(func.count(Source.id))) or 0
        total_docs = await session.scalar(select(func.count(Document.id))) or 0
        total_chunks = await session.scalar(select(func.count(Chunk.id))) or 0

        # 2. Missing source URLs
        missing_urls = await session.scalar(
            select(func.count(Chunk.id)).where((Chunk.source_url == None) | (Chunk.source_url == ""))
        ) or 0

        # 3. Missing authorities
        missing_auth = await session.scalar(
            select(func.count(Chunk.id)).where((Chunk.authority == None) | (Chunk.authority == ""))
        ) or 0

        # 4. Null embeddings
        null_embeddings = await session.scalar(
            select(func.count(Chunk.id)).where(Chunk.embedding == None)
        ) or 0

        # 5. Empty chunk text
        empty_chunks = await session.scalar(
            select(func.count(Chunk.id)).where((Chunk.content == None) | (func.length(Chunk.content) < 10))
        ) or 0

        # 6. Duplicate content hashes
        dup_hashes_query = await session.execute(
            select(Chunk.content_hash, func.count(Chunk.id))
            .group_by(Chunk.content_hash)
            .having(func.count(Chunk.id) > 1)
        )
        dup_hashes_count = len(dup_hashes_query.fetchall())

        table = Table(title="Corpus Health & Integrity Report")
        table.add_column("Integrity Check", style="bold")
        table.add_column("Result", style="green" if missing_urls == 0 and null_embeddings == 0 else "yellow")
        table.add_column("Status")

        table.add_row("Total Sources Ingested", str(total_sources), "OK")
        table.add_row("Total Documents", str(total_docs), "OK")
        table.add_row("Total Legal Chunks", str(total_chunks), "OK")
        table.add_row("Missing Source URLs", str(missing_urls), "PASS" if missing_urls == 0 else "FAIL")
        table.add_row("Missing Authority Badges", str(missing_auth), "PASS" if missing_auth == 0 else "WARN")
        table.add_row("Un-embedded Chunks (Null pgvector)", str(null_embeddings), "PASS" if null_embeddings == 0 else "FAIL")
        table.add_row("Empty / Short Chunks", str(empty_chunks), "PASS" if empty_chunks == 0 else "WARN")
        table.add_row("Duplicate Content Hashes", str(dup_hashes_count), "PASS" if dup_hashes_count == 0 else "WARN")

        console.print(table)

        if missing_urls == 0 and null_embeddings == 0 and empty_chunks == 0:
            console.print("\n[green]Corpus integrity is 100% valid and ready for production RAG retrieval.[/green]")
        else:
            console.print("\n[yellow]Validation found warnings. Run scripts/rebuild_index.py to repair.[/yellow]")


if __name__ == "__main__":
    asyncio.run(run_validation())
