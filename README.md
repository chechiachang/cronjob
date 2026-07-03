# cronjob

A collection of scheduled jobs triggered by GitHub Actions. Each subdirectory contains an independent cronjob.

## Setup

1. **Fork or clone** this repository.
2. Add the required secrets in **Settings → Secrets and variables → Actions**:
   - `FIRECRAWL_API_KEY` — your [Firecrawl](https://www.firecrawl.dev/) API key (used by the `ithome-cfp` job).
3. The workflows run automatically on schedule, or you can trigger them manually from the **Actions** tab.

## Jobs

### ithome-cfp

Scrapes CFP (Call for Proposals) events from [iThome](https://www.ithome.com.tw/cfp) using [Firecrawl](https://docs.firecrawl.dev/introduction).  
**Schedule:** Daily at 08:00 UTC

#### Requirements

- Python 3.11+
- A [Firecrawl](https://www.firecrawl.dev/) API key

#### Usage

1. Add your Firecrawl API key to `.env` in the repository root:
   ```
   FIRECRAWL_API_KEY=<your-key>
   ```

2. Install dependencies and run:
   ```bash
   cd ithome-cfp
   pip install -r requirements.txt
   python main.py
   ```

To save output to a file, set `OUTPUT_FILE`:
   ```bash
   OUTPUT_FILE=events.json python main.py
   ```

#### Output format

```json
{
  "source": "https://www.ithome.com.tw/cfp",
  "total": 3,
  "events": [
    {
      "raw": "...",
      "title": "Event title",
      "url": "https://...",
      "dates": ["2024-01-01", "2024-03-31"]
    }
  ]
}
```

#### GitHub Actions

This job is triggered automatically by the [ithome-cfp workflow](./.github/workflows/ithome-cfp.yml).  
The `FIRECRAWL_API_KEY` secret must be set in the repository settings.

## Structure

```
.
├── .github/
│   └── workflows/
│       └── ithome-cfp.yml   # GitHub Actions workflow
└── ithome-cfp/
    ├── main.py              # Scraper script
    └── requirements.txt     # Python dependencies
```
