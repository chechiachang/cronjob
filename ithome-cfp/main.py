"""
ithome-cfp: Scrape CFP (Call for Proposals) events from www.ithome.com.tw/cfp
using the Firecrawl API and print the results as JSON.

Usage:
    FIRECRAWL_API_KEY=<key> python main.py

Environment variables:
    FIRECRAWL_API_KEY  - Required. Your Firecrawl API key.
    OUTPUT_FILE        - Optional. Path to write JSON output (default: stdout).
"""

import json
import os
import re
import sys

from firecrawl import FirecrawlApp

CFP_URL = "https://www.ithome.com.tw/cfp"


def scrape_cfp(api_key: str) -> dict:
    """Scrape the iThome CFP page using Firecrawl and return the raw result.

    Args:
        api_key: A valid Firecrawl API key.

    Returns:
        A dictionary from Firecrawl containing at least:
          - "markdown": the page content as Markdown text.
          - "links": a list of link objects found on the page (each with
            "url"/"href" and optionally "text" keys).

    Raises:
        Exception: if the Firecrawl API call fails.
    """
    app = FirecrawlApp(api_key=api_key)

    result = app.scrape_url(
        CFP_URL,
        params={
            "formats": ["markdown", "links"],
        },
    )
    return result


def parse_events(scrape_result: dict) -> list[dict]:
    """Extract CFP event entries from a Firecrawl scrape result.

    Args:
        scrape_result: Dictionary returned by ``scrape_cfp()``.  Expected keys:
          - "markdown" (str): page content as Markdown.
          - "links" (list): link objects with "url"/"href" and optional "text".

    Returns:
        A list of event dictionaries.  Each dictionary contains:
          - "raw" (str): the original Markdown line.
          - "title" (str, optional): text of the first Markdown link on the line.
          - "url" (str, optional): href of the first Markdown link on the line.
          - "dates" (list[str], optional): date strings in YYYY-MM-DD / YYYY/MM/DD
            format found on the line.
    """
    events = []

    markdown = scrape_result.get("markdown", "")
    links = scrape_result.get("links", [])

    # Build a lookup of link text -> href from the links list
    link_map: dict[str, str] = {}
    for link in links:
        if isinstance(link, dict):
            href = link.get("url") or link.get("href", "")
            text = link.get("text", "")
        else:
            href = str(link)
            text = ""
        if href:
            link_map[text.strip()] = href

    # Parse markdown lines to find event entries.
    # iThome CFP pages typically list events as markdown list items with a
    # title, date range, and link.  We collect each non-empty line that looks
    # like an event (contains a markdown link or a date pattern).
    date_pattern = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}")
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for line in markdown.splitlines():
        line = line.strip()
        if not line:
            continue

        found_links = link_pattern.findall(line)
        has_date = bool(date_pattern.search(line))

        if found_links or has_date:
            entry: dict = {"raw": line}

            if found_links:
                entry["title"] = found_links[0][0]
                entry["url"] = found_links[0][1]

            # Extract all date-like strings
            dates = date_pattern.findall(line)
            if dates:
                entry["dates"] = dates

            events.append(entry)

    return events


def main() -> None:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("Error: FIRECRAWL_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Scraping {CFP_URL} ...", file=sys.stderr)
    scrape_result = scrape_cfp(api_key)

    events = parse_events(scrape_result)

    output = {
        "source": CFP_URL,
        "total": len(events),
        "events": events,
    }

    output_file = os.environ.get("OUTPUT_FILE")
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Results written to {output_file}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
