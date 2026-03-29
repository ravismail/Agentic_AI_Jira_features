"""Content scraping from URLs, Confluence pages, and file uploads."""

import logging
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("scraper")


class ContentScraper:
    """Scrapes content from URLs, Confluence REST API, and uploaded files."""

    CONFLUENCE_PAGE_RE = re.compile(r"/wiki/.*pages/(\d+)")
    MAX_CHARS = 15000
    MAX_ROWS = 200

    def scrape_url(self, url: str, username: str = None, token: str = None) -> str:
        """Scrape text content from a URL. Uses Confluence REST API when detected."""
        match = self.CONFLUENCE_PAGE_RE.search(url)
        if match and username and token:
            logger.info("Detected Confluence page (id=%s), using REST API", match.group(1))
            return self._scrape_confluence(url, match.group(1), username, token)
        logger.info("Scraping generic URL: %s", url)
        return self._scrape_generic(url, username, token)

    def _scrape_confluence(
        self, url: str, page_id: str, username: str, token: str
    ) -> str:
        """Fetch Confluence page body via REST API."""
        base = url.split("/wiki")[0]
        api_url = f"{base}/wiki/rest/api/content/{page_id}?expand=body.storage"
        resp = requests.get(api_url, auth=(username, token), timeout=30)
        resp.raise_for_status()
        html = resp.json()["body"]["storage"]["value"]
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)[: self.MAX_CHARS]

    def _scrape_generic(
        self, url: str, username: str = None, token: str = None
    ) -> str:
        """Scrape a generic web page. Pass auth only to atlassian.net domains."""
        auth = None
        if username and token and "atlassian.net" in url:
            auth = (username, token)
        resp = requests.get(url, auth=auth, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[: self.MAX_CHARS]

    def parse_file(self, uploaded_file) -> tuple[list[dict], list[str]]:
        """Parse CSV/Excel file. Returns (rows as dicts, column names)."""
        logger.info("Parsing file: %s", uploaded_file.name)
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel.")

        if df.empty:
            raise ValueError("The uploaded file is empty.")

        # Limit rows
        if len(df) > self.MAX_ROWS:
            df = df.head(self.MAX_ROWS)

        columns = list(df.columns)
        # Use first 3 columns
        use_cols = columns[: min(3, len(columns))]
        rows = []
        for _, row in df[use_cols].iterrows():
            rows.append({col: str(row[col]) for col in use_cols})

        logger.info("Parsed %d rows, columns: %s", len(rows), use_cols)
        return rows, use_cols

    def format_file_content(self, rows: list[dict]) -> str:
        """Format parsed file rows into a text string for LLM consumption."""
        lines = []
        for i, row in enumerate(rows, 1):
            values = " | ".join(row.values())
            lines.append(f"Row {i}: {values}")
        return "\n".join(lines)
