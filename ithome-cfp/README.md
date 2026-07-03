# ithome-cfp

A cronjob that scrapes the [iThome CFP (Call for Proposals)](https://www.ithome.com.tw/cfp) page using [Firecrawl](https://docs.firecrawl.dev/introduction) and outputs the events as JSON.

## Requirements

- Python 3.11+
- A [Firecrawl](https://www.firecrawl.dev/) API key

## Usage

```bash
cd ithome-cfp
pip install -r requirements.txt
FIRECRAWL_API_KEY=<your-key> python main.py
```

To save the output to a file:

```bash
FIRECRAWL_API_KEY=<your-key> OUTPUT_FILE=events.json python main.py
```

## Output format

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

## GitHub Actions

This job is triggered automatically by the [`ithome-cfp`](../.github/workflows/ithome-cfp.yml) workflow.  
The `FIRECRAWL_API_KEY` secret must be set in the repository settings.
