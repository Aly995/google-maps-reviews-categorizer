# Google Maps Scraper

A Python scraper that reads a list of keywords, searches them on Google Maps, and extracts business data (name, address, phone, website, hours, stars, review count) plus individual reviews — exporting everything to Excel and CSV.

## Features

- Searches Google Maps by keyword list
- Exports place data to Excel (`.xls`)
- Scrapes reviews sorted by newest and saves them to CSV
- Optional AI-powered review analysis via `review_analyzer.py`
- Supports **English** and **Spanish** Google Maps interfaces
- Multi-threaded scraping (4 threads by default)

## Project Structure

```
google_maps_scraper/
├── main.py                 # Entry point — run this
├── maps_data_scraper.py    # Core Selenium scraping logic
├── place_maps.py           # MapsPlace data model
├── export_data.py          # Excel export
├── review_analyzer.py      # AI review analysis (requires OpenAI API key)
├── analyze_reviews.py      # CLI tool for manual review analysis
├── dashboard_generator.py  # Dashboard generation from review data
├── utils.py                # Helper utilities
├── requirements.txt        # Python dependencies
└── .env.example            # Example environment variables
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/google_maps_scraper.git
cd google_maps_scraper
```

### 2. Create and activate a virtual environment

**Windows:**
```bash
python -m venv env
.\env\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your OpenAI API Key (optional — for AI review analysis)

The review analyzer uses OpenAI's API to perform sentiment analysis on scraped reviews. To enable it:

1. Get your API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. Copy the example env file:
   ```bash
   # Windows
   copy .env.example .env

   # macOS/Linux
   cp .env.example .env
   ```

3. Open the `.env` file and paste your key:
   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   ```

## Usage

Run the main script and follow the prompts:

```bash
python main.py
```

You will be asked:

1. **Language** — Enter `ES` (Spanish) or `EN` (English) to match the Google Maps locale you want to scrape.
2. **Output folder** — Folder where Excel, images, and CSV files will be saved. Example: `C:\output\`
3. **Keywords file** — Path to a `.txt` file with one search keyword per line. Example: `C:\places.txt`
4. **Auto-analyze reviews** — `Y` to run AI sentiment analysis on the scraped reviews, `N` to skip.

### Keywords file format

One search term per line:

```
Starbucks New York
McDonald's London
Eiffel Tower Paris
```

## Output

| File | Description |
|------|-------------|
| `00_output.xls` | All place data (name, address, phone, etc.) |
| `<keyword>_reviews.csv` | Reviews for each place |
| `<keyword>.jpg` | Cover image for each place |

## Requirements

- Python 3.8+
- Google Chrome installed
- ChromeDriver is managed automatically via `webdriver-manager`

## License

MIT
