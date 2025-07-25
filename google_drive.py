import os
import logging
from typing import Optional
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from config import Config

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Service for Google Drive integration"""
    
    def __init__(self):
        self.config = Config()
        self.service = None
        self.folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')
        
        # Initialize Google Drive service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive API service"""
        try:
            credentials_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
            if not credentials_json:
                logger.warning("GOOGLE_DRIVE_CREDENTIALS not found, Google Drive integration disabled")
                return
            
            # Parse credentials from environment variable
            credentials_info = json.loads(credentials_json)
            
            # Define the required scopes
            scopes = ['https://www.googleapis.com/auth/drive.file']
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                credentials_info, 
                scopes=scopes
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
            self.service = None
    
    def upload_file(self, local_file_path: str, folder_name: str) -> str:
        """Upload file to Google Drive and return shareable URL"""
        if not self.service:
            logger.warning("Google Drive service not available")
            return ""
        
        try:
            # Get or create folder
            folder_id = self._get_or_create_folder(folder_name)
            if not folder_id:
                logger.error("Could not get or create folder")
                return ""
            
            # Extract filename from path
            filename = os.path.basename(local_file_path)
            
            # File metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            # Upload file
            media = MediaFileUpload(
                local_file_path,
                mimetype='text/csv',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            # Make file shareable (anyone with link can view)
            self.service.permissions().create(
                fileId=file['id'],
                body={
                    'role': 'reader',
                    'type': 'anyone'
                }
            ).execute()
            
            logger.info(f"File uploaded successfully: {file['webViewLink']}")
            return file['webViewLink']
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive: {e}")
            return ""
    
    def _get_or_create_folder(self, folder_name: str) -> Optional[str]:
        """Get existing folder or create new one"""
        try:
            # Check if folder exists
            parent_folder_id = self.folder_id or 'root'
            
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and parents in '{parent_folder_id}'"
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                # Folder exists, return its ID
                return items[0]['id']
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                logger.info(f"Created new folder: {folder_name}")
                return folder['id']
                
        except Exception as e:
            logger.error(f"Error getting or creating folder: {e}")
            return None
    
    def list_files_in_folder(self, folder_name: str) -> list:
        """List all files in a specific folder"""
        if not self.service:
            return []
        
        try:
            folder_id = self._get_or_create_folder(folder_name)
            if not folder_id:
                return []
            
            query = f"parents in '{folder_id}'"
            results = self.service.files().list(q=query, fields='files(id,name,createdTime,webViewLink)').execute()
            items = results.get('files', [])
            
            return items
            
        except Exception as e:
            logger.error(f"Error listing files in folder: {e}")
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.service:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_file_metadata(self, file_id: str) -> dict:
        """Get metadata for a specific file"""
        if not self.service:
            return {}
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,createdTime,modifiedTime,webViewLink'
            ).execute()
            
            return file
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return {}
