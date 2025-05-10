# Project Architecture: Playwright Full-Page Screenshot Automator

This document outlines the technical architecture of the Playwright Full-Page Screenshot Automator, a Python application designed to automate the process of capturing full-page screenshots of web pages listed in a Google Sheet, uploading them to Google Drive, and updating the sheet with the Drive links.

## 1. Core Components

The application is structured into several key Python modules:

*   **`main_playwright.py`**: The main executable script that orchestrates the entire process. It handles:
    *   Loading environment variables.
    *   Initializing logging.
    *   Reading URLs from the specified Google Sheet.
    *   Iterating through URLs, processing each one.
    *   Calling utility functions for Playwright actions, Google Drive uploads, and Google Sheet updates.
    *   Error handling and reporting.

*   **`utils/playwright_utils.py`**: Contains all Playwright-specific logic.
    *   `take_playwright_screenshot()`: Manages browser and page instances, navigates to a URL, handles cookie consent banners, captures a full-page screenshot, and closes the page.
    *   It loads browser context with cookies for the session.

*   **`utils/gdrive_utils.py`**: Handles interactions with Google Drive.
    *   `upload_to_gdrive()`: Uploads a given file (screenshot) to a specified folder in Google Drive and returns the shareable link.
    *   Manages authentication with Google Drive using service account credentials.

*   **`utils/gsheet_utils.py`**: Manages interactions with Google Sheets.
    *   `read_urls()`: Fetches the list of URLs to process from the specified sheet and range.
    *   `update_gsheet_with_link()`: Writes the Google Drive link back to the appropriate cell in the sheet for a processed URL.
    *   `is_url_processed()`: Checks if a URL has already been processed by looking for an existing Google Drive link in the sheet.
    *   Manages authentication with Google Sheets using service account credentials.

*   **`utils/__init__.py`**: Makes the `utils` directory a Python package.

## 2. Configuration

*   **`.env` (via `.env.example`)**: Stores sensitive information and project-specific configurations:
    *   `GOOGLE_SHEET_ID`: The ID of the Google Sheet containing the URLs.
    *   `URL_RANGE`: The specific sheet and cell range for URLs and status (e.g., `Sheet1!B2:C`).
    *   `GDRIVE_FOLDER_ID`: The ID of the Google Drive folder where screenshots will be uploaded.
    *   `GOOGLE_APPLICATION_CREDENTIALS`: Path to the Google Cloud service account JSON key file.
    *   `LOG_LEVEL`: Configures the logging verbosity (e.g., INFO, DEBUG).
    *   `SCREENSHOT_DIR`: Local directory to temporarily store screenshots before upload.
    *   `INTER_URL_WAIT_SECONDS`: Wait time between processing URLs.
    *   `PLAYWRIGHT_TIMEOUT`: General timeout for Playwright operations (e.g., page load).
    *   `COOKIE_FILE_PATH`: Path to the `cookies.json` file.

*   **`cookies.json`**: Stores browser cookies to be loaded by Playwright, which can help with authentication or bypassing cookie consent pop-ups for certain sites.

## 3. Workflow

1.  **Initialization**:
    *   The `main_playwright.py` script is executed.
    *   Environment variables are loaded from the `.env` file.
    *   Logging is configured (both console and file output).
    *   Google API clients (Sheets and Drive) are authenticated using the provided credentials.
    *   Playwright browser is launched, and a browser context is created. Cookies from `cookies.json` are loaded into this context.

2.  **URL Processing Loop**:
    *   The script calls `gsheet_utils.read_urls()` to fetch the list of URLs from the Google Sheet defined by `GOOGLE_SHEET_ID` and `URL_RANGE`.
    *   For each URL:
        *   It checks if the URL has already been processed using `gsheet_utils.is_url_processed()` (by looking for a GDrive link in column C).
        *   If not processed:
            *   A new page is created within the persistent Playwright browser context.
            *   `playwright_utils.take_playwright_screenshot()` is called:
                *   Navigates to the URL.
                *   Attempts to click an "Accept all cookies" button if present.
                *   Takes a full-page screenshot.
                *   Saves the screenshot locally to the directory specified by `SCREENSHOT_DIR`.
                *   Closes the page.
            *   If the screenshot is successful:
                *   `gdrive_utils.upload_to_gdrive()` uploads the local screenshot file to the specified Google Drive folder.
                *   `gsheet_utils.update_gsheet_with_link()` writes the returned Google Drive link to the corresponding row in column C of the Google Sheet.
                *   The local screenshot file is deleted.
            *   Appropriate logging messages are generated for success or failure at each step.
        *   A configured delay (`INTER_URL_WAIT_SECONDS`) is observed before processing the next URL.

3.  **Completion & Cleanup**:
    *   After processing all URLs, the Playwright browser is closed.
    *   Log handlers are flushed.
    *   The script exits.

## 4. Key Technologies

*   **Python 3**: Core programming language.
*   **Playwright**: For browser automation and screenshot capture. Chosen for its robustness and ability to handle modern web features.
*   **Google Sheets API**: For reading URLs and writing back results.
*   **Google Drive API**: For storing the captured screenshots.
*   **`python-dotenv`**: For managing environment variables.
*   **`logging`**: Python's built-in logging module for tracking script execution and errors.

## 5. Error Handling and Logging

*   The script implements try-except blocks to catch potential errors during web navigation, screenshotting, API interactions, and file operations.
*   Detailed logs are written to `playwright_processing_log.txt`, including timestamps, log levels, and messages.
*   A simpler log output (message only) is displayed on the console.
*   If a URL fails, the error is logged, and the script moves to the next URL.

## 6. Directory Structure (Illustrative)

```
playwright-ai-agent/
├── .env.example
├── .gitignore
├── ARCHITECTURE.MD
├── main_playwright.py
├── README.MD
├── requirements_playwright.txt
├── cookies.json
├── playwright_processing_log.txt (generated at runtime)
├── screenshots/ (generated at runtime, if not immediately deleted)
└── utils/
    ├── __init__.py
    ├── gdrive_utils.py
    ├── gsheet_utils.py
    └── playwright_utils.py
```

This architecture aims for modularity, maintainability, and robustness in automating the screenshot process. 