import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GOOGLE_DRIVE_CREDENTIALS = os.environ.get('GOOGLE_DRIVE_CREDENTIALS', '')
    NOTION_INTEGRATION_SECRET = os.environ.get('NOTION_INTEGRATION_SECRET', '')
    NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID', '')
    
    # Email settings
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'leads@aileadgen.com')
    
    # Lead processing settings
    DEFAULT_LEAD_BATCH_SIZE = 50
    DEDUPLICATION_WINDOW_DAYS = 30
    
    # Client plan configurations
    PLAN_CONFIGURATIONS = {
        'basic': {
            'max_leads': 100,
            'exclusive_option': False,
            'ai_personalization': False,
            'priority': 3
        },
        'pro': {
            'max_leads': 250,
            'exclusive_option': True,
            'ai_personalization': True,
            'priority': 2
        },
        'premium': {
            'max_leads': 500,
            'exclusive_option': True,
            'ai_personalization': True,
            'priority': 1
        }
    }
    
    # Scheduling settings
    DEFAULT_PROCESSING_TIME = '09:00'
    TIMEZONE = 'UTC'
    
    # File storage settings
    GOOGLE_DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')
    LOCAL_STORAGE_PATH = 'LeadDeliveries'
    
    # Commission tracking
    COMMISSION_RATES = {
        'basic': 0.10,
        'pro': 0.15,
        'premium': 0.20
    }
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        required_vars = [
            'GEMINI_API_KEY',
            'NOTION_INTEGRATION_SECRET',
            'NOTION_DATABASE_ID',
            'EMAIL_USER',
            'EMAIL_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
