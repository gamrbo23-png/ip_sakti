#!/usr/bin/env python3
"""
IP-SAKTI Sahayak — Index Rebuilder Script
Recomputes BGE-M3 embeddings and PostgreSQL full-text search tsvectors
for all stored chunks in the database.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from rich.console import Console
from sqlalchemy import select, text

console = Console()


async def rebuild_indexes():
    from app.config import get_settings
    from app.database import get_db_context
    from app.models.models import Chunk
    from app.services.embedding_service import get_embedding_service

    console.print("\n[bold blue]IP-SAKTI Sahayak — Rebuilding Embeddings & Full-Text Search Indexes[/bold blue]\n")

    emb_service = get_embedding_service()

    async with get_db_context() as session:
        result = await session.execute(select(Chunk).order_by(Chunk.id))
        chunks = result.scalars().all()

        console.print(f"Total chunks to process: [bold]{len(chunks)}[/bold]")
        if not chunks:
            console.print("[yellow]No chunks found in database. Ingest sources first via scripts/ingest.py[/yellow]")
            return

        batch_size = 16
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            embeddings = emb_service.encode(texts)

            for chunk_obj, emb_vec in zip(batch, embeddings):
                chunk_obj.embedding = emb_vec

            console.print(f"Processed chunks [{min(i + batch_size, len(chunks))}/{len(chunks)}]")

        await session.commit()

        # Re-index PostgreSQL HNSW index
        console.print("\n[bold]Rebuilding pgvector HNSW index and GIN FTS index...[/bold]")
        await session.execute(text("REINDEX INDEX ix_chunks_embedding_hnsw;"))
        await session.execute(text("REINDEX INDEX ix_chunks_search_vector;"))
        await session.commit()

        console.print("\n[green]✓ All embeddings and PostgreSQL vector/FTS indexes successfully re-indexed![/green]")


if __name__ == "__main__":
    asyncio.run(rebuild_indexes())
