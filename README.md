# cronjob

A collection of scheduled jobs triggered by GitHub Actions. Each subdirectory contains an independent cronjob.

## Jobs

| Directory | Description | Schedule |
|-----------|-------------|----------|
| [ithome-cfp](./ithome-cfp/) | Scrapes CFP events from [iThome](https://www.ithome.com.tw/cfp) using [Firecrawl](https://docs.firecrawl.dev/introduction) | Daily at 08:00 UTC |

## Setup

1. **Fork or clone** this repository.
2. Add the required secrets in **Settings → Secrets and variables → Actions**:
   - `FIRECRAWL_API_KEY` — your [Firecrawl](https://www.firecrawl.dev/) API key (used by the `ithome-cfp` job).
3. The workflows run automatically on schedule, or you can trigger them manually from the **Actions** tab.

## Structure

```
.
├── .github/
│   └── workflows/
│       └── ithome-cfp.yml   # GitHub Actions workflow
└── ithome-cfp/
    ├── main.py              # Scraper script
    ├── requirements.txt     # Python dependencies
    └── README.md            # Job-specific docs
```
