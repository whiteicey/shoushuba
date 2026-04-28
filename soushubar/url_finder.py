from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

MAX_REDIRECTS = 10


def find_current_url(entry_url: str) -> str:
    current = entry_url
    visited = set()

    for attempt in range(MAX_REDIRECTS):
        if current in visited:
            raise RuntimeError(f"Redirect loop detected at: {current}")
        visited.add(current)

        try:
            resp = requests.get(current, timeout=15)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch {current}: {e}")

        if "forum.php" in resp.text:
            return current.rstrip("/")

        soup = BeautifulSoup(resp.text, "html.parser")
        next_url = _extract_redirect(soup, current, resp)

        if next_url is None or next_url == current:
            raise RuntimeError(
                f"Could not find forum URL after {attempt + 1} redirects "
                f"from {entry_url}. Last URL: {current}"
            )

        print(f"[URL Finder] {current} -> {next_url}", flush=True)
        current = next_url

    raise RuntimeError(
        f"Exceeded max redirects ({MAX_REDIRECTS}) from {entry_url}"
    )


def _extract_redirect(soup: BeautifulSoup, current_url: str, resp) -> str | None:
    redirect_meta = soup.find("meta", attrs={"http-equiv": "refresh"})
    if redirect_meta:
        content = redirect_meta.get("content", "")
        match = re.search(r"url=(.+?)(?:;|$)", content, re.IGNORECASE)
        if match:
            next_url = match.group(1).strip().strip("'\"")
            return _normalize_url(next_url, current_url)

    link = soup.find("a")
    if link:
        href = link.get("href", "")
        if href and href != current_url:
            return _normalize_url(href, current_url)

    return None


def _normalize_url(url: str, base_url: str) -> str:
    if not url.startswith("http"):
        url = urljoin(base_url, url)
    return url.rstrip("/")
