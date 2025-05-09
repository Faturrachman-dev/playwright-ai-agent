import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.exceptions import DefaultCredentialsError

# Configure logging for this module
logger = logging.getLogger(__name__) # Use a module-specific logger

def get_drive_service():
    """Authenticates and returns a Google Drive API service object."""
    try:
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
        if not os.path.exists(creds_path):
            logger.error(f"Credentials file not found at {creds_path}. Please ensure GOOGLE_APPLICATION_CREDENTIALS is set and the file exists.")
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        logger.info("Google Drive service initialized successfully.")
        return service
    except DefaultCredentialsError as e:
        logger.error(f"Google Default Credentials Error: {e}. This usually means the GOOGLE_APPLICATION_CREDENTIALS environment variable is not set correctly or the file is missing/invalid.")
        raise
    except Exception as e:
        logger.error(f"Error initializing Google Drive service: {e}", exc_info=True)
        raise

def upload_file(service, file_path, folder_id):
    """Uploads a file to a specific Google Drive folder and returns the file ID and web link."""
    try:
        if not os.path.exists(file_path):
            logger.error(f"File to upload not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        
        logger.info(f"Starting upload for {file_path} to folder {folder_id}...")
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        logger.info(f"File uploaded successfully: ID='{file_id}', Link='{web_link}'")
        print(f"📤 File uploaded to Drive: {web_link}") # Keep this for user feedback
        return file_id, web_link
    except Exception as e:
        logger.error(f"Error uploading file {file_path} to Google Drive: {e}", exc_info=True)
        # print(f"❌ Error uploading {os.path.basename(file_path)} to Drive: {e}") # Covered by logger
        raise 