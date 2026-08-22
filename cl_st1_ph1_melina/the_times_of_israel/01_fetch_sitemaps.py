from __future__ import annotations

import csv
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests


SOURCE_ID = "the_times_of_israel"
BASE_DIR = Path(__file__).resolve().parent

ROBOTS_PATH = BASE_DIR / "docs" / "robots.txt"

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SITEMAPS_DIR = RAW_DIR / "sitemaps"
LOGS_DIR = DATA_DIR / "logs"

FETCH_LOG_PATH = LOGS_DIR / "sitemap_fetch_log.csv"
SITEMAP_INDEX_LOG_PATH = LOGS_DIR / "sitemap_index_children.csv"

REQUEST_DELAY_SECONDS = 3

HEADERS = {
    "User-Agent": "Academic research corpus collection; contact: laelgelc@outlook.com"
}

SITEMAP_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}


def ensure_directories() -> None:
    SITEMAPS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def project_relative_path(path: Path) -> str:
    """
    Return a path relative to this source directory, so logs remain portable
    across EC2, local machines, and future project locations.
    """
    return str(path.relative_to(BASE_DIR))


def extract_sitemap_urls_from_robots(robots_path: Path) -> list[str]:
    if not robots_path.exists():
        raise FileNotFoundError(f"robots.txt not found: {robots_path}")

    sitemap_urls: list[str] = []

    for line in robots_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        if not stripped.lower().startswith("sitemap:"):
            continue

        sitemap_url = stripped.split(":", 1)[1].strip()

        if sitemap_url:
            sitemap_urls.append(sitemap_url)

    return sorted(set(sitemap_urls))


def filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    filename = Path(parsed.path).name

    if not filename:
        filename = "sitemap.xml"

    return filename


def local_path_for_sitemap(url: str) -> Path:
    return SITEMAPS_DIR / filename_from_url(url)


def fetch_url(url: str) -> tuple[int | None, str | None, str | None]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        return response.status_code, response.text, None
    except requests.RequestException as exc:
        return None, None, str(exc)


def fetch_and_save_sitemap(url: str) -> dict[str, str]:
    local_path = local_path_for_sitemap(url)

    row = {
        "source_id": SOURCE_ID,
        "url": url,
        "local_path": project_relative_path(local_path),
        "http_status": "",
        "fetch_status": "",
        "error_message": "",
    }

    if local_path.exists():
        row["fetch_status"] = "already_exists"
        return row

    status_code, text, error_message = fetch_url(url)

    if status_code is not None:
        row["http_status"] = str(status_code)

    if error_message:
        row["fetch_status"] = "failed"
        row["error_message"] = error_message
        return row

    if status_code != 200 or text is None:
        row["fetch_status"] = "failed"
        row["error_message"] = f"HTTP {status_code}"
        return row

    local_path.write_text(text, encoding="utf-8")
    row["fetch_status"] = "saved"

    return row


def parse_sitemap_index_file(path: Path) -> list[dict[str, str]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []

    if not root.tag.endswith("sitemapindex"):
        return []

    children: list[dict[str, str]] = []

    for sitemap_node in root.findall("sm:sitemap", SITEMAP_NS):
        loc = sitemap_node.findtext("sm:loc", default="", namespaces=SITEMAP_NS).strip()
        lastmod = sitemap_node.findtext("sm:lastmod", default="", namespaces=SITEMAP_NS).strip()

        if not loc:
            continue

        children.append(
            {
                "sitemap_index_file": path.name,
                "child_sitemap_url": loc,
                "child_sitemap_lastmod": lastmod,
                "child_sitemap_file": filename_from_url(loc),
            }
        )

    return children


def save_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ensure_directories()

    print(f"Reading sitemap declarations from: {project_relative_path(ROBOTS_PATH)}")
    top_level_sitemap_urls = extract_sitemap_urls_from_robots(ROBOTS_PATH)

    print(f"Found {len(top_level_sitemap_urls)} sitemap URL(s) in robots.txt:")
    for url in top_level_sitemap_urls:
        print(f"  - {url}")

    fetch_log: list[dict[str, str]] = []
    sitemap_index_children: list[dict[str, str]] = []

    print("\nFetching top-level sitemaps from robots.txt...")
    for sitemap_url in top_level_sitemap_urls:
        print(f"Fetching: {sitemap_url}")
        row = fetch_and_save_sitemap(sitemap_url)
        fetch_log.append(row)
        time.sleep(REQUEST_DELAY_SECONDS)

    print("\nChecking top-level sitemaps for child sitemap indexes...")
    for sitemap_url in top_level_sitemap_urls:
        local_path = local_path_for_sitemap(sitemap_url)

        if not local_path.exists():
            continue

        children = parse_sitemap_index_file(local_path)

        if not children:
            continue

        print(f"{local_path.name}: found {len(children)} child sitemap(s)")
        sitemap_index_children.extend(children)

    child_sitemap_urls = sorted(
        {
            row["child_sitemap_url"]
            for row in sitemap_index_children
            if row.get("child_sitemap_url")
        }
    )

    print(f"\nFetching {len(child_sitemap_urls)} child sitemap(s) from sitemap index...")
    for child_sitemap_url in child_sitemap_urls:
        print(f"Fetching: {child_sitemap_url}")
        row = fetch_and_save_sitemap(child_sitemap_url)
        fetch_log.append(row)
        time.sleep(REQUEST_DELAY_SECONDS)

    save_csv(
        FETCH_LOG_PATH,
        fetch_log,
        [
            "source_id",
            "url",
            "local_path",
            "http_status",
            "fetch_status",
            "error_message",
        ],
    )

    save_csv(
        SITEMAP_INDEX_LOG_PATH,
        sitemap_index_children,
        [
            "sitemap_index_file",
            "child_sitemap_url",
            "child_sitemap_lastmod",
            "child_sitemap_file",
        ],
    )

    print(f"\nSaved sitemap fetch log to: {project_relative_path(FETCH_LOG_PATH)}")
    print(f"Saved sitemap index children log to: {project_relative_path(SITEMAP_INDEX_LOG_PATH)}")
    print(f"Saved sitemap XML files under: {project_relative_path(SITEMAPS_DIR)}")


if __name__ == "__main__":
    main()