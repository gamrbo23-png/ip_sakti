#!/usr/bin/env python3
"""
IP-SAKTI Sahayak — Master Ingestion Script
Runs the full document ingestion pipeline from the command line.

Usage:
  python scripts/ingest.py                    # Ingest all sources
  python scripts/ingest.py --domain patent    # Ingest only patent sources
  python scripts/ingest.py --refresh          # Force re-ingest all
  python scripts/ingest.py --source src_patent_act_1970  # Ingest specific source
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()


@click.command()
@click.option("--domain", "-d", multiple=True, help="IP domain to ingest (can specify multiple)")
@click.option("--source", "-s", help="Specific source ID to ingest")
@click.option("--refresh", "-r", is_flag=True, help="Force re-ingest even if hash unchanged")
@click.option("--dry-run", is_flag=True, help="Show what would be ingested without actually doing it")
def main(domain, source, refresh, dry_run):
    """IP-SAKTI Sahayak — Document Ingestion Pipeline"""
    asyncio.run(_run(list(domain), source, refresh, dry_run))


async def _run(domains, source_id, refresh, dry_run):
    from app.config import get_settings
    from app.database import init_extensions
    from app.ingestion.source_registry import get_source_registry
    from app.logging_config import configure_logging

    settings = get_settings()
    configure_logging(settings.log_level)

    console.print("\n[bold blue]IP-SAKTI Sahayak — Document Ingestion[/bold blue]")
    console.print(f"Environment: {settings.app_env}")
    console.print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}\n")

    # Initialize DB extensions
    try:
        await init_extensions()
        console.print("[green]✓ Database extensions initialized[/green]")
    except Exception as exc:
        console.print(f"[red]✗ Database initialization failed: {exc}[/red]")
        console.print("Ensure PostgreSQL is running and DATABASE_URL is correct.")
        sys.exit(1)

    # Run migrations
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent / "backend",
            capture_output=True, text=True
        )
        if result.returncode == 0:
            console.print("[green]✓ Database migrations applied[/green]")
        else:
            console.print(f"[yellow]⚠ Migration output: {result.stderr}[/yellow]")
    except Exception as exc:
        console.print(f"[yellow]⚠ Could not run migrations: {exc}[/yellow]")

    # Load source registry
    registry = get_source_registry()
    sources = registry.get_all()

    if source_id:
        entry = registry.get_by_id(source_id)
        if not entry:
            console.print(f"[red]Source '{source_id}' not found in registry[/red]")
            sys.exit(1)
        sources = [entry]
    elif domains:
        sources = [s for s in sources if s.domain in domains]

    if not sources:
        console.print("[yellow]No sources matched the specified criteria[/yellow]")
        return

    # Display what will be ingested
    table = Table(title="Sources to Ingest")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Domain")
    table.add_column("Type")
    table.add_column("Authority")

    for s in sources:
        table.add_row(s.id, s.name[:60], s.domain, s.document_type, s.authority[:40])

    console.print(table)
    console.print(f"\nTotal: {len(sources)} sources")

    if dry_run:
        console.print("\n[yellow]Dry run — not actually ingesting[/yellow]")
        return

    # Run ingestion
    console.print("\n[bold]Starting ingestion...[/bold]\n")

    from app.ingestion.pipeline import ingest_source_entry

    results = []
    for i, entry in enumerate(sources, 1):
        console.print(f"[{i}/{len(sources)}] {entry.name[:70]}...")
        result = await ingest_source_entry(entry, force_refresh=refresh)
        results.append(result)

        status = result.get("status", "unknown")
        if status == "success":
            console.print(
                f"  [green]✓ Success[/green] — "
                f"{result.get('chunks_created', 0)} chunks, "
                f"{result.get('duplicates_skipped', 0)} dupes"
            )
        elif status == "skipped":
            console.print(f"  [yellow]○ Skipped[/yellow] — {result.get('reason', 'unchanged')}")
        else:
            console.print(f"  [red]✗ Failed[/red] — {result.get('error', 'unknown')[:100]}")

    # Summary report
    console.print("\n[bold]═══ Ingestion Report ═══[/bold]")
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    total_dupes = sum(r.get("duplicates_skipped", 0) for r in results)

    console.print(f"Documents attempted:  {len(sources)}")
    console.print(f"[green]Successful:           {successful}[/green]")
    console.print(f"[yellow]Skipped (unchanged):  {skipped}[/yellow]")
    console.print(f"[red]Failed:               {failed}[/red]")
    console.print(f"Chunks created:       {total_chunks}")
    console.print(f"Duplicates skipped:   {total_dupes}")
    console.print(f"Embeddings generated: {total_chunks}")

    if failed > 0:
        console.print("\n[yellow]Failed sources:[/yellow]")
        for r in results:
            if r.get("status") == "failed":
                console.print(f"  - {r.get('url', 'unknown')}: {r.get('error', '')[:80]}")


if __name__ == "__main__":
    main()
