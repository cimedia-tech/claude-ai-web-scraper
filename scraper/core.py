import asyncio
import json
import random
from pathlib import Path
from typing import Type
from pydantic import BaseModel

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import settings
from .cache import URLCache
from .preprocessor import truncate_to_token_limit
from .claude_client import ClaudeExtractor
from .schemas import SCHEMA_MAP

console = Console()


def _browser_config() -> BrowserConfig:
    """Stealth headless browser config with randomized fingerprint."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    return BrowserConfig(
        headless=True,
        java_script_enabled=True,
        user_agent=random.choice(user_agents),
        viewport_width=random.choice([1280, 1366, 1440, 1920]),
        viewport_height=random.choice([720, 768, 900, 1080]),
    )


def _crawl_config() -> CrawlerRunConfig:
    """Crawl4AI run config — Fit Markdown output (50–80% token reduction)."""
    content_filter = PruningContentFilter(
        threshold=0.48,
        threshold_type="fixed",
        min_word_threshold=10,
    )
    md_generator = DefaultMarkdownGenerator(content_filter=content_filter)
    return CrawlerRunConfig(
        markdown_generator=md_generator,
        excluded_tags=["script", "style", "nav", "footer", "header",
                       "aside", "form", "noscript", "iframe"],
        remove_overlay_elements=True,
        magic=True,           # Crawl4AI built-in anti-bot stealth
        simulate_user=True,   # Human-like mouse/scroll simulation
        page_timeout=settings.page_timeout_ms,
    )


class Scraper:
    """
    Core scraper — orchestrates Crawl4AI + Claude extraction pipeline.

    Flow:
      URL → cache check → Crawl4AI (Fit Markdown) → Claude Haiku extraction
          → Pydantic validation → JSON output → SQLite cache write
    """

    def __init__(self, schema_type: str = "lead"):
        self.schema: Type[BaseModel] = SCHEMA_MAP.get(schema_type, SCHEMA_MAP["lead"])
        self.cache = URLCache()
        self.extractor = ClaudeExtractor(cache=self.cache)
        self._results: list[BaseModel] = []

    async def _init(self):
        await self.cache.init()
        await self.cache.purge_expired()

    async def scrape_url(self, url: str, instruction: str) -> list[BaseModel]:
        """Scrape a single URL and return extracted results."""
        # 1. Check cache first
        cached = await self.cache.get(url)
        if cached:
            console.print(f"  [dim]↩ Cache hit:[/] {url[:60]}")
            raw = json.loads(cached)
            return [self.schema(**item) for item in raw]

        # 2. Crawl with Crawl4AI
        browser_cfg = _browser_config()
        run_cfg = _crawl_config()

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        if not result.success:
            console.print(f"  [red]✗ Crawl failed:[/] {url} — {result.error_message}")
            return []

        # 3. Use Fit Markdown (already token-pruned by Crawl4AI)
        content = result.fit_markdown or result.markdown or ""
        if not content.strip():
            console.print(f"  [yellow]⚠ Empty content:[/] {url}")
            return []

        # 4. Final token guard
        content = truncate_to_token_limit(content)

        # 5. Claude extraction
        try:
            items = await self.extractor.extract(
                content=content,
                schema=self.schema,
                url=url,
                instruction=instruction,
            )
        except Exception as e:
            console.print(f"  [red]✗ Extraction error:[/] {e}")
            return []

        # 6. Cache result
        raw_list = [item.model_dump() for item in items]
        await self.cache.set(url, json.dumps(raw_list))

        # 7. Rate limit delay (anti-bot)
        delay = random.uniform(settings.request_delay_min, settings.request_delay_max)
        await asyncio.sleep(delay)

        return items

    async def run(
        self,
        urls: list[str],
        instruction: str = "Extract all relevant items from this page.",
        output_file: str = None,
    ) -> list[dict]:
        """Run scraper across a list of URLs. Returns all results as dicts."""
        await self._init()
        self._results = []

        # Enforce page limit
        urls = urls[:settings.max_pages_per_run]

        console.print(f"\n[bold gold1]🕷  Claude AI Scraper[/] — {len(urls)} URLs | "
                      f"Model: [cyan]{settings.claude_model}[/]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Scraping...", total=len(urls))

            for url in urls:
                progress.update(task, description=f"[cyan]{url[:55]}[/]")
                items = await self.scrape_url(url, instruction)
                self._results.extend([item.model_dump() for item in items])
                progress.advance(task)

        # Save output
        out_path = self._save(output_file)
        total_cost = await self.cache.total_cost()

        console.print(f"\n[bold green]✓ Done[/] — "
                      f"{len(self._results)} records extracted\n"
                      f"[dim]Output:[/] {out_path}\n"
                      f"[dim]Total API cost (session):[/] [yellow]${total_cost:.5f}[/]\n")

        return self._results

    def _save(self, output_file: str = None) -> Path:
        out_dir = Path(settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = Path(output_file) if output_file else out_dir / f"results_{ts}.json"
        path.write_text(json.dumps(self._results, indent=2, ensure_ascii=False))
        return path
