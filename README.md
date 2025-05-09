# Playwright AI Agent - Full Page Screenshotter

This project uses Playwright to automate taking full-page screenshots of web pages listed in a Google Sheet, uploads them to Google Drive, and updates the sheet with the Drive links.

## Features

- Reads URLs from a specified Google Sheet range.
- Takes full-page screenshots using Playwright.
- Handles cookie loading from a `cookies.json` file.
- Attempts to automatically accept cookie consent banners.
- Uploads screenshots to a specified Google Drive folder.
- Updates the Google Sheet with direct links to the uploaded screenshots.
- Logs processing details and errors to a file (`playwright_processing_log.txt` by default).

## Prerequisites

- Python 3.8+
- Access to Google Drive and Google Sheets APIs.
- A Google Cloud Platform project with the Drive and Sheets APIs enabled.
- Service account credentials (`credentials.json`) for accessing Google APIs.

## Setup

1.  **Clone the repository (or create the project directory `playwright-ai-agent`).**

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements_playwright.txt
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```
    (This will install default browsers like Chromium, Firefox, WebKit. Chromium is used by default in this script).

5.  **Set up Google Credentials:**
    *   Follow the Google Cloud documentation to create a service account and download its JSON key file.
    *   Rename the key file to `credentials.json` and place it in the `playwright-ai-agent` root directory.
    *   Ensure this service account has necessary permissions for the target Google Sheet (edit access) and Google Drive folder (edit or write access).

6.  **Prepare `cookies.json` (Optional but Recommended):**
    *   If the target websites require login or have specific cookie-based states you want to capture, use a browser extension (like "Get cookies.txt" or similar, making sure it can export in JSON format compatible with Selenium/Playwright) to export cookies for the relevant domains after logging in manually.
    *   Save these cookies as `cookies.json` in the `playwright-ai-agent` root directory.

7.  **Configure Environment Variables:**
    *   Create a `.env` file in the `playwright-ai-agent` root directory by copying `.env.example`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your specific details:
        *   `SPREADSHEET_ID`: The ID of your Google Sheet.
        *   `URL_RANGE`: The range in your sheet where URLs are listed (e.g., `Sheet1!B2:B`). Column B for URLs, Column C for GDrive links is assumed by default for `is_url_processed` and `update_metadata`.
        *   `FOLDER_ID`: The ID of the Google Drive folder where screenshots will be uploaded.
        *   `COOKIES_PATH`: Path to your cookies file (default: `cookies.json`).
        *   `SCREENSHOTS_DIR`: Temp directory for screenshots (default: `screenshots`).
        *   `LOG_FILE`: Path for the log file (default: `playwright_processing_log.txt`).
        *   `GOOGLE_APPLICATION_CREDENTIALS`: Path to your credentials file (default: `credentials.json`).
        *   `INTER_URL_DELAY_SECONDS`: Delay between processing URLs (default: `3.0`).
        *   `HEADLESS_BROWSER`: Run Playwright in headless mode (`True` or `False`, default: `True`).

## Running the Script

Once setup is complete, run the main script from the `playwright-ai-agent` directory:

```bash
python main_playwright.py
```

## Project Structure

(Refer to `STRUCTURE.md` for a detailed directory layout)

## Logging

- Detailed logs are saved to `playwright_processing_log.txt` (or as configured in `.env`).
- Logs are also printed to the console.

## Notes

- Ensure your Google Sheet is set up with URLs in the specified `URL_RANGE` (e.g., column B). The script expects to write GDrive links to the next column (e.g., column C).
- The `is_url_processed` function in `utils/gsheet_utils.py` checks column C by default to see if a GDrive link already exists. Modify this if your sheet structure is different.
