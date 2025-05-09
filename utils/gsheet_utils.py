import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.exceptions import DefaultCredentialsError

# Configure logging for this module
logger = logging.getLogger(__name__) # Use a module-specific logger

def get_sheets_service():
    """Authenticates and returns a Google Sheets API service object."""
    try:
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
        if not os.path.exists(creds_path):
            logger.error(f"Credentials file not found at {creds_path}.")
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        logger.info("Google Sheets service initialized successfully.")
        return service
    except DefaultCredentialsError as e:
        logger.error(f"Google Default Credentials Error for Sheets: {e}.")
        raise
    except Exception as e:
        logger.error(f"Error initializing Google Sheets service: {e}", exc_info=True)
        raise

def read_urls(service, spreadsheet_id, range_name):
    """Reads URLs from the specified Google Sheet range."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        urls = [row[0] for row in values if row and row[0].strip()] # Assuming URLs are in the first column of the range
        logger.info(f"Read {len(urls)} URLs from sheet range {range_name}.")
        return urls
    except Exception as e:
        logger.error(f"Error reading URLs from sheet {spreadsheet_id}, range {range_name}: {e}", exc_info=True)
        # print(f"❌ Error reading URLs from Google Sheet: {e}") # Covered by logger
        return []

def is_url_processed(service, spreadsheet_id, sheet_name: str, sheet_row_number: int, column_to_check='C'):
    """Checks if a URL in a given row (1-indexed) on a specific sheet has a GDrive link in the specified column."""
    try:
        range_to_check = f"{sheet_name}!{column_to_check}{sheet_row_number}"
        logger.debug(f"Checking if URL is processed at: {range_to_check}")
        
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_to_check).execute()
        values = result.get('values', [])
        
        if values and values[0] and values[0][0].strip().startswith('https://drive.google.com'):
            logger.info(f"URL in row {sheet_row_number} already processed (GDrive link found in {column_to_check}).")
            return True
        logger.info(f"No GDrive link found in {column_to_check}{sheet_row_number} for URL in row {sheet_row_number}.")
        return False
    except Exception as e:
        logger.error(f"Error checking if URL in row {sheet_row_number} is processed: {e}", exc_info=True)
        # If there's an error, assume not processed to be safe, or handle as critical
        return False 

def update_metadata(service, spreadsheet_id, range_name, values):
    """Updates cell(s) in the Google Sheet with provided values."""
    try:
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name, 
            valueInputOption='USER_ENTERED', body=body).execute()
        logger.info(f"Sheet updated successfully: {result.get('updatedCells')} cells updated in range {range_name}.")
        # print(f"📝 Sheet range {range_name} updated.") # Reduced verbosity, covered by logger
        return result
    except Exception as e:
        logger.error(f"Error updating sheet {spreadsheet_id}, range {range_name}: {e}", exc_info=True)
        # print(f"❌ Error updating Google Sheet: {e}") # Covered by logger
        raise 