"""
ithome-cfp: Scrape CFP (Call for Proposals) events from www.ithome.com.tw/cfp
using the Firecrawl API and print the results as JSON.

Usage:
    python main.py

Environment variables (read from ../.env or system env):
    FIRECRAWL_API_KEY  - Required. Your Firecrawl API key.
    OUTPUT_FILE        - Optional. Path to write JSON output (default: stdout).
"""

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv(Path(__file__).parent.parent / ".env")

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
        formats=["markdown", "links"],
    )
    return result


def scrape_event_page(api_key: str, event_url: str) -> dict:
    """Scrape an individual event page to extract details.

    Args:
        api_key: A valid Firecrawl API key.
        event_url: The URL of the event page.

    Returns:
        A dictionary with event details or empty dict if scrape fails.
    """
    try:
        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(
            event_url,
            formats=["markdown"],
        )
        return result if result else {}
    except Exception as e:
        print(f"Warning: Failed to scrape event page {event_url}: {e}", file=sys.stderr)
        return {}


def parse_chinese_date(date_str: str) -> str:
    """Convert Chinese date format to YYYY-MM-DD.

    Args:
        date_str: Date string in format "YYYY 年 MM 月 DD 日"

    Returns:
        Date string in YYYY-MM-DD format or original if parse fails.
    """
    try:
        match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
    except Exception:
        pass
    return date_str


def extract_event_details(markdown: str) -> dict:
    """Extract event details from event page markdown.

    Args:
        markdown: The markdown content of the event page.

    Returns:
        A dictionary with extracted details: location, dates, cfp_deadline, event_date, cfp_link.
    """
    details = {}

    iso_date_pattern = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}")
    chinese_date_pattern = re.compile(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日")
    cfp_link_pattern = re.compile(
        r"https://(docs\.google\.com|forms\.gle|[^/]+\.typeform\.com|airtable\.com|surveyheart\.com)[^\s\)]*"
    )

    iso_dates = iso_date_pattern.findall(markdown)
    chinese_dates = chinese_date_pattern.findall(markdown)

    all_dates = []
    all_dates.extend(iso_dates)
    all_dates.extend([parse_chinese_date(d) for d in chinese_dates])

    if all_dates:
        details["dates"] = list(set(all_dates))

    cfp_links = cfp_link_pattern.findall(markdown)
    if cfp_links:
        cfp_match = re.search(cfp_link_pattern, markdown)
        if cfp_match:
            details["cfp_link"] = cfp_match.group(0)

    lines = markdown.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()

        if "投稿截止" in line or "cfp" in line_lower or "call for" in line_lower:
            deadline = line.strip().replace("**", "").replace("##", "").strip()
            if deadline and len(deadline) > 5:
                details["cfp_deadline"] = deadline

        if "活動日期" in line or "event date" in line_lower:
            event_date = line.strip().replace("**", "").replace("##", "").strip()
            if event_date and len(event_date) > 5:
                details["event_date"] = event_date

        if "地點" in line or "location" in line_lower or "venue" in line_lower:
            location = line.strip().replace("**", "").replace("##", "").strip()
            if location and len(location) > 5:
                details["location"] = location

    return details


def is_event_entry(line: str, title: str) -> bool:
    """Check if a line is likely a real CFP event, not navigation/image/UI text."""
    if not title or len(title) < 5:
        return False

    skip_patterns = [
        "移至",  # skip to
        "主內容",  # main content
        "![",  # image markdown
        "footer",  # footer
        "sidebar",  # sidebar
        "menu",  # menu
        "breadcrumb",  # breadcrumb
    ]

    title_lower = title.lower()
    for pattern in skip_patterns:
        if pattern in title_lower or pattern in line:
            return False

    return True


def parse_events(scrape_result) -> list[dict]:
    """Extract CFP event entries from a Firecrawl scrape result.

    Args:
        scrape_result: Firecrawl Document object or dict with:
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

    if isinstance(scrape_result, dict):
        markdown = scrape_result.get("markdown", "")
        links = scrape_result.get("links", [])
    else:
        markdown = getattr(scrape_result, "markdown", "")
        links = getattr(scrape_result, "links", [])

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
            title = found_links[0][0] if found_links else ""

            if not is_event_entry(line, title):
                continue

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


def print_summary(output: dict) -> None:
    print("=" * 70, file=sys.stderr)
    print(f"✅ Scraping completed: {output['total']} events found", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    for i, event in enumerate(output["events"], 1):
        print(f"\n📌 Event #{i}", file=sys.stderr)

        if event.get("title"):
            print(f"   Title:      {event['title']}", file=sys.stderr)

        if event.get("url"):
            print(f"   URL:        {event['url']}", file=sys.stderr)

        if event.get("location"):
            print(f"   Location:   {event['location']}", file=sys.stderr)

        if event.get("cfp_deadline"):
            print(f"   CFP Close:  {event['cfp_deadline']}", file=sys.stderr)

        if event.get("event_date"):
            print(f"   Event Date: {event['event_date']}", file=sys.stderr)

        if event.get("dates"):
            dates_str = " | ".join(event["dates"])
            print(f"   All Dates:  {dates_str}", file=sys.stderr)

        if event.get("cfp_link"):
            print(f"   CFP Link:   {event['cfp_link']}", file=sys.stderr)

    print("\n" + "=" * 70, file=sys.stderr)


def write_github_summary(output: dict) -> None:
    """Write event summary to GitHub job summary for visibility on run page."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    with open(summary_file, "a", encoding="utf-8") as f:
        f.write("# 📊 iThome CFP Scraping Results\n\n")
        f.write(f"**Total Events Found:** {output['total']}\n\n")

        if output["total"] == 0:
            f.write("No events found.\n")
            return

        f.write("## Events\n\n")
        for i, event in enumerate(output["events"], 1):
            f.write(f"### {i}. {event.get('title', 'Untitled')}\n\n")

            if event.get("url"):
                f.write(f"**Event Page:** [{event['url']}]({event['url']})\n\n")

            if event.get("location"):
                f.write(f"📍 **Location:** {event['location']}\n\n")

            if event.get("cfp_deadline"):
                f.write(f"📝 **CFP Deadline:** {event['cfp_deadline']}\n\n")

            if event.get("event_date"):
                f.write(f"📅 **Event Date:** {event['event_date']}\n\n")

            if event.get("dates"):
                f.write(f"🗓️ **All Dates:**\n")
                for date in event["dates"]:
                    f.write(f"- {date}\n")
                f.write("\n")

            if event.get("cfp_link"):
                f.write(f"🔗 **Submit CFP:** [{event['cfp_link']}]({event['cfp_link']})\n\n")

            f.write("---\n\n")


def main() -> None:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("Error: FIRECRAWL_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"🔄 Scraping {CFP_URL} ...", file=sys.stderr)
    scrape_result = scrape_cfp(api_key)

    events = parse_events(scrape_result)

    print(f"📖 Scraping {len(events)} event pages for details...", file=sys.stderr)
    for event in events:
        if event.get("url"):
            event_page = scrape_event_page(api_key, event["url"])
            if event_page:
                markdown = (
                    event_page.get("markdown", "")
                    if isinstance(event_page, dict)
                    else getattr(event_page, "markdown", "")
                )
                details = extract_event_details(markdown)
                event.update(details)

    output = {
        "source": CFP_URL,
        "total": len(events),
        "events": events,
    }

    output_file = os.environ.get("OUTPUT_FILE")
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Results written to {output_file}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    print_summary(output)
    write_github_summary(output)


if __name__ == "__main__":
    main()
