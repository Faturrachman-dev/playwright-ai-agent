```
└── 📁playwright-ai-agent
    ├── 📁screenshots           # Temporary storage for screenshots before upload
    ├── 📁utils                 # Utility modules
    │   ├── __init__.py         # Makes 'utils' a Python package
    │   ├── gdrive_utils.py     # Functions for Google Drive interaction
    │   ├── gsheet_utils.py     # Functions for Google Sheets interaction
    │   └── playwright_utils.py # Core Playwright automation functions
    ├── .env                    # Local environment variables (ignored by git)
    ├── .env.example            # Example environment variables file
    ├── .gitignore              # Specifies intentionally untracked files that Git should ignore
    ├── cookies.json            # (User-provided) Cookies for websites, if needed
    ├── credentials.json        # (User-provided) Google Cloud service account credentials
    ├── main_playwright.py      # Main executable script for the Playwright version
    ├── playwright_processing_log.txt # Log file for processing details and errors
    ├── README.md               # Project overview, setup, and usage instructions
    ├── requirements_playwright.txt # Python package dependencies
    └── STRUCTURE.md            # This file: describes the project directory structure
```
