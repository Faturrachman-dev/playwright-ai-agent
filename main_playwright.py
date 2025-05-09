import os
import logging
import time
import re
import random # For inter-URL delay
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Import utility modules
from utils import gdrive_utils, gsheet_utils, playwright_utils

# Load environment variables from .env file
load_dotenv()

# --- Configuration from Environment Variables ---
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
URL_RANGE = os.getenv('URL_RANGE') # e.g., Sheet1!B2:B
FOLDER_ID = os.getenv('FOLDER_ID') # Google Drive Folder ID
COOKIES_PATH = os.getenv('COOKIES_PATH')
SCREENSHOTS_DIR = os.getenv('SCREENSHOTS_DIR', 'screenshots')
LOG_FILE = os.getenv('LOG_FILE', 'playwright_processing_log.txt')
INTER_URL_DELAY_SECONDS = float(os.getenv('INTER_URL_DELAY_SECONDS', '3.0')) # Default to 3 seconds
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'True').lower() == 'true'

# --- Global Logging Setup ---
# Ensure logs directory exists if LOG_FILE includes a path
log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# File handler for detailed logs
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO) # Or logging.DEBUG for even more detail in file

logging.basicConfig(
    level=logging.INFO, # Set root logger level
    handlers=[
        file_handler
        # Console output will be handled by explicit print() statements
    ],
    force=True # Override any other logging configurations
)
logger = logging.getLogger(__name__)

def main():
    # Print to console for this high-level message, also log it for file record
    print("--- Starting Playwright Screenshot Processing ---")
    logger.info("--- Starting Playwright Screenshot Processing ---")
    start_time = time.time()

    # --- Validate Essential Configuration ---
    missing_vars = []
    if not SPREADSHEET_ID: missing_vars.append("SPREADSHEET_ID")
    if not URL_RANGE: missing_vars.append("URL_RANGE")
    if not FOLDER_ID: missing_vars.append("FOLDER_ID")
    if not COOKIES_PATH: missing_vars.append("COOKIES_PATH") # Make it optional with a warning?
    
    if missing_vars:
        error_msg = f"Missing critical environment variables: {', '.join(missing_vars)}. Please check your .env file."
        # Log critical for file, print for console
        logger.critical(error_msg)
        print(f"❌ {error_msg}")
        return

    # Log configuration details to file only
    logger.info(f"Configuration: Spreadsheet ID: {SPREADSHEET_ID}, URL Range: {URL_RANGE}, Drive Folder ID: {FOLDER_ID}")
    logger.info(f"Cookies Path: {COOKIES_PATH}, Screenshots Dir: {SCREENSHOTS_DIR}, Headless: {HEADLESS_BROWSER}")

    # --- Initialize Services and Playwright ---
    playwright_manager = None
    browser = None
    context = None

    try:
        print("\n🔄 Initializing Google services...")
        drive_service = gdrive_utils.get_drive_service()
        sheets_service = gsheet_utils.get_sheets_service()
        print("✅ Google services initialized.")
        # Redundant logger.info for this already printed message can be removed if desired

        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        logger.info(f"Screenshots will be saved in: {os.path.abspath(SCREENSHOTS_DIR)}")

        print("\n🚀 Initializing Playwright browser...")
        playwright_manager = sync_playwright().start()
        browser = playwright_manager.chromium.launch(headless=HEADLESS_BROWSER)
        context = browser.new_context(
            user_agent=playwright_utils.COMMON_USER_AGENT,
            viewport={'width': 1920, 'height': 1080} # Default viewport, can be adjusted if needed
        )
        if COOKIES_PATH and os.path.exists(COOKIES_PATH):
            playwright_utils.load_playwright_cookies(context, COOKIES_PATH) # This function logs and prints selectively
        elif COOKIES_PATH:
            logger.warning(f"COOKIES_PATH ({COOKIES_PATH}) is set but file not found. Proceeding without loading cookies.")
            print(f"⚠️ Cookies file not found at {COOKIES_PATH}. Proceeding without pre-loaded cookies.") # Console feedback
        else:
            logger.info("COOKIES_PATH not set. Proceeding without pre-loaded cookies.")
            print("🍪 COOKIES_PATH not set. No cookies will be pre-loaded.") # Console feedback
        print("✅ Playwright browser and context initialized.") # Console feedback

        # --- Read URLs from Google Sheet ---
        print("\n📋 Reading URLs from spreadsheet...")
        urls_to_process = gsheet_utils.read_urls(sheets_service, SPREADSHEET_ID, URL_RANGE)
        
        if not urls_to_process:
            msg = "⚠️ No URLs found to process in the specified sheet range."
            print(msg) # Console feedback
            logger.warning(msg) # File log
            return
        
        total_urls = len(urls_to_process)
        logger.info(f"Found {total_urls} URLs to process.") # File log only
        print(f"📊 Found {total_urls} URLs to process.") # Console feedback
        
        successful_screenshots = 0
        failed_screenshots = 0
        skipped_urls = 0

        # --- Process Each URL ---
        # Determine starting row number and sheet name from URL_RANGE (e.g., Sheet2!B2:B -> sheet_name='Sheet2', start_row_in_sheet=2)
        range_match = re.match(r'([^\'!]+)\![A-Z]+([0-9]+)', URL_RANGE, re.IGNORECASE)
        if not range_match:
            logger.critical(f"Could not parse sheet name and start row from URL_RANGE: '{URL_RANGE}'. Expected format like 'SheetName!A1:A'.")
            print(f"❌ Invalid URL_RANGE format: {URL_RANGE}")
            return
        
        parsed_sheet_name = range_match.group(1).strip("'") # Remove potential single quotes around sheet name
        start_row_in_sheet = int(range_match.group(2))
        logger.info(f"Interpreted URL_RANGE '{URL_RANGE}' as: Sheet='{parsed_sheet_name}', Start Row={start_row_in_sheet}") # File log only

        for i, url in enumerate(urls_to_process):
            current_loop_index = i + 1
            current_sheet_row = start_row_in_sheet + i # 0-indexed i + start_row for 1-indexed sheet
            
            print(f"\n[ {current_loop_index}/{total_urls} ] Processing URL: {url} (Sheet Row: {current_sheet_row})") # Console progress
            logger.info(f"Processing URL ({current_loop_index}/{total_urls}): {url} (Sheet Row: {current_sheet_row})") # Detailed log for file

            # Basic URL validation
            if not url or not url.strip().startswith(('http://', 'https://')):
                invalid_msg = f"Invalid or empty URL format: '{url}'. Skipping."
                print(f"❌ {invalid_msg}") # Console error
                logger.error(invalid_msg) # File log
                failed_screenshots += 1
                continue

            # Check if URL is already processed (e.g., GDrive link exists)
            # Assuming column C is for GDrive links as per previous context.
            if gsheet_utils.is_url_processed(sheets_service, SPREADSHEET_ID, parsed_sheet_name, current_sheet_row, column_to_check='C'):
                skip_msg = f"Skipping URL (already processed - GDrive link found in {parsed_sheet_name}!C{current_sheet_row}): {url}"
                print(f"⏩ {skip_msg}") # Console skip message
                logger.info(f"⏩ {skip_msg}") # File log
                skipped_urls +=1
                continue
            
            screenshot_filename = playwright_utils.generate_screenshot_filename(url)
            screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
            
            screenshot_success = playwright_utils.take_playwright_screenshot(context, url, screenshot_path)

            if screenshot_success:
                logger.info(f"Screenshot captured successfully: {screenshot_filename}") # File log
                print(f"✅ Screenshot captured: {screenshot_filename}") # Console feedback
                
                try:
                    print(f"📤 Uploading {screenshot_filename} to Google Drive...") # Console feedback
                    _file_id, web_link = gdrive_utils.upload_file(drive_service, screenshot_path, FOLDER_ID) # gdrive_utils handles its own print for success
                    logger.info(f"Uploaded {screenshot_filename} to {web_link}.") # File log
                    
                    print(f"📝 Updating Google Sheet (Row {current_sheet_row}, Col C) with GDrive link...") # Console feedback
                    metadata_range = f'{parsed_sheet_name}!C{current_sheet_row}'
                    metadata_values = [[web_link]]
                    gsheet_utils.update_metadata(sheets_service, SPREADSHEET_ID, metadata_range, metadata_values)
                    logger.info(f"Sheet updated for {url} ({parsed_sheet_name}!C{current_sheet_row}) with {web_link}.") # File log
                    successful_screenshots += 1
                except Exception as e_upload_sheet:
                    err_msg = f"Error during Drive upload or Sheet update for {url}: {e_upload_sheet}"
                    print(f"❌ {err_msg}") # Console error
                    logger.error(err_msg, exc_info=True) # File log
                    failed_screenshots += 1
                finally:
                    if os.path.exists(screenshot_path):
                        try:
                            os.remove(screenshot_path)
                            logger.info(f"Cleaned up local screenshot: {screenshot_path}")
                        except OSError as e_remove:
                            logger.error(f"Error removing local screenshot {screenshot_path}: {e_remove}")
            else:
                err_msg = f"Failed to capture screenshot for URL: {url}"
                print(f"❌ {err_msg}") # Console error
                logger.error(err_msg) # take_playwright_screenshot logs details already
                failed_screenshots += 1
            
            if current_loop_index < total_urls:
                logger.info(f"Waiting {INTER_URL_DELAY_SECONDS:.2f}s before next URL.") # File log only
                print(f"⏳ Waiting {INTER_URL_DELAY_SECONDS:.2f} seconds...") # Console feedback
                time.sleep(INTER_URL_DELAY_SECONDS)
        
    except Exception as e_main:
        crit_msg = f"Critical error in main processing loop: {e_main}"
        print(f"❌ {crit_msg}") # Console critical error
        logger.critical(crit_msg, exc_info=True) # File log
    finally:
        if browser:
            logger.info("Closing Playwright browser.") # File log
            print("\n🚪 Closing Playwright browser...") # Console feedback
            browser.close()
        if playwright_manager:
            logger.info("Stopping Playwright manager.") # File log
            playwright_manager.stop()
            print("🛑 Playwright manager stopped.") # Console feedback
        
        # --- Final Summary ---
        end_time = time.time()
        total_time = end_time - start_time
        # Log detailed summary to file
        logger.info(f"--- Playwright Screenshot Processing Ended. Total time: {total_time:.2f} seconds ---")
        logger.info(f"Summary: Total URLs={total_urls}, Successful={successful_screenshots}, Skipped={skipped_urls}, Failed={failed_screenshots}")
        
        # Print clean summary to console
        print(f"\n✨ Processing Complete! Took {total_time:.2f} seconds.")
        print(f"📊 Summary:")
        print(f"   Processed: {total_urls}")
        print(f"   ✅ Successful Screenshots & Uploads: {successful_screenshots}")
        print(f"   ⏩ Skipped (already processed): {skipped_urls}")
        print(f"   ❌ Failed: {failed_screenshots}")

if __name__ == "__main__":
    main() 