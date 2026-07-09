"""Claude AI Web Scraper — CLI entry point."""
import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="scraper",
    help="Claude AI Web Scraper — powered by Crawl4AI + Claude Haiku",
    no_args_is_help=True,
)
console = Console()


@app.command()
def scrape(
    urls: list[str] = typer.Argument(..., help="One or more URLs to scrape"),
    schema: str = typer.Option("lead", "--schema", "-s",
                               help="Extraction schema: lead | product | article | generic"),
    instruction: str = typer.Option(
        "Extract all relevant items from this page.",
        "--instruction", "-i",
        help="Natural language extraction instruction for Claude",
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o",
                                          help="Output JSON file path"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max pages per run"),
):
    """Scrape one or more URLs and extract structured data with Claude."""
    from scraper.core import Scraper
    from scraper.config import settings

    # Override page limit if set via CLI
    settings.max_pages_per_run = limit

    scraper = Scraper(schema_type=schema)
    results = asyncio.run(scraper.run(
        urls=urls,
        instruction=instruction,
        output_file=output,
    ))

    if results:
        _print_table(results[:10], schema)
        if len(results) > 10:
            console.print(f"[dim]... and {len(results) - 10} more records in output file[/]")


@app.command()
def cost():
    """Show total estimated Claude API cost for all runs."""
    from scraper.cache import URLCache
    cache = URLCache()

    async def _show():
        await cache.init()
        total = await cache.total_cost()
        console.print(f"\n[bold]Total estimated Claude API cost:[/] [yellow]${total:.5f}[/]\n")

    asyncio.run(_show())


@app.command()
def clear_cache():
    """Clear expired URL cache entries."""
    from scraper.cache import URLCache
    cache = URLCache()

    async def _clear():
        await cache.init()
        await cache.purge_expired()
        console.print("[green]✓ Expired cache entries purged.[/]")

    asyncio.run(_clear())


def _print_table(results: list[dict], schema: str):
    if not results:
        return
    table = Table(title=f"Extracted {schema.title()} Data (first 10)",
                  style="dim", header_style="bold cyan")
    keys = list(results[0].keys())[:6]  # show max 6 cols
    for k in keys:
        table.add_column(k.replace("_", " ").title(), max_width=30, overflow="fold")
    for row in results:
        table.add_row(*[str(row.get(k) or "") for k in keys])
    console.print(table)


if __name__ == "__main__":
    app()
