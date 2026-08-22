from __future__ import annotations

import csv
import logging
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
RUN_LOG_PATH = LOGS_DIR / "01_fetch_sitemaps.log"

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


def configure_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("timesofisrael_fetch_sitemaps")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


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
    logger = configure_logging(RUN_LOG_PATH)

    logger.info("Starting sitemap fetch programme.")
    logger.info("Run log: %s", project_relative_path(RUN_LOG_PATH))

    logger.info("Reading sitemap declarations from: %s", project_relative_path(ROBOTS_PATH))
    top_level_sitemap_urls = extract_sitemap_urls_from_robots(ROBOTS_PATH)

    logger.info("Found %s sitemap URL(s) in robots.txt.", len(top_level_sitemap_urls))
    for url in top_level_sitemap_urls:
        logger.info("Sitemap declared in robots.txt: %s", url)

    fetch_log: list[dict[str, str]] = []
    sitemap_index_children: list[dict[str, str]] = []

    logger.info("Fetching top-level sitemaps from robots.txt.")
    for sitemap_url in top_level_sitemap_urls:
        logger.info("Fetching top-level sitemap: %s", sitemap_url)
        row = fetch_and_save_sitemap(sitemap_url)
        fetch_log.append(row)
        logger.info(
            "Fetch result: url=%s status=%s fetch_status=%s error=%s",
            row["url"],
            row["http_status"],
            row["fetch_status"],
            row["error_message"],
        )
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("Checking top-level sitemaps for child sitemap indexes.")
    for sitemap_url in top_level_sitemap_urls:
        local_path = local_path_for_sitemap(sitemap_url)

        if not local_path.exists():
            logger.warning("Local sitemap file does not exist: %s", project_relative_path(local_path))
            continue

        children = parse_sitemap_index_file(local_path)

        if not children:
            logger.info("No child sitemaps found in: %s", local_path.name)
            continue

        logger.info("%s: found %s child sitemap(s)", local_path.name, len(children))
        sitemap_index_children.extend(children)

    child_sitemap_urls = sorted(
        {
            row["child_sitemap_url"]
            for row in sitemap_index_children
            if row.get("child_sitemap_url")
        }
    )

    logger.info("Fetching %s child sitemap(s) from sitemap index.", len(child_sitemap_urls))
    for child_sitemap_url in child_sitemap_urls:
        logger.info("Fetching child sitemap: %s", child_sitemap_url)
        row = fetch_and_save_sitemap(child_sitemap_url)
        fetch_log.append(row)
        logger.info(
            "Fetch result: url=%s status=%s fetch_status=%s error=%s",
            row["url"],
            row["http_status"],
            row["fetch_status"],
            row["error_message"],
        )
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

    logger.info("Saved sitemap fetch log to: %s", project_relative_path(FETCH_LOG_PATH))
    logger.info("Saved sitemap index children log to: %s", project_relative_path(SITEMAP_INDEX_LOG_PATH))
    logger.info("Saved sitemap XML files under: %s", project_relative_path(SITEMAPS_DIR))
    logger.info("Finished sitemap fetch programme.")


if __name__ == "__main__":
    main()