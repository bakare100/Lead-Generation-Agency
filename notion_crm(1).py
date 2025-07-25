import os
import logging
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class NotionCRM:
    """Service for Notion CRM integration"""
    
    def __init__(self):
        self.config = Config()
        self.notion_token = os.environ.get('NOTION_INTEGRATION_SECRET', '')
        self.database_id = os.environ.get('NOTION_DATABASE_ID', '')
        self.base_url = 'https://api.notion.com/v1'
        
        # Headers for Notion API
        self.headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
    
    def log_delivery(self, delivery_data: Dict[str, Any]) -> bool:
        """Log delivery to Notion database"""
        if not self.notion_token or not self.database_id:
            logger.warning("Notion credentials not configured")
            return False
        
        try:
            # Prepare data for Notion (matching your actual database schema)
            properties = {
                'Name': {
                    'title': [
                        {
                            'text': {
                                'content': f"Delivery to {delivery_data['client_name']}"
                            }
                        }
                    ]
                },
                'Client Name': {
                    'rich_text': [
                        {
                            'text': {
                                'content': delivery_data['client_name']
                            }
                        }
                    ]
                },
                'Lead Count': {
                    'number': delivery_data['leads_count']
                },
                'Files Path': {
                    'rich_text': [
                        {
                            'text': {
                                'content': delivery_data.get('file_path', '')
                            }
                        }
                    ]
                },
                'Drive URL': {
                    'url': delivery_data.get('google_drive_url', '')
                },
                'Delivery Date': {
                    'date': {
                        'start': self._format_date(delivery_data.get('delivered_at', delivery_data.get('created_at', datetime.now().isoformat())))
                    }
                },
                'Status': {
                    'select': {
                        'name': delivery_data.get('status', 'Delivered')
                    }
                }
            }
            
            # Create page in Notion database
            url = f'{self.base_url}/pages'
            data = {
                'parent': {'database_id': self.database_id},
                'properties': properties
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Successfully logged delivery to Notion: {delivery_data['client_name']}")
                return True
            else:
                logger.error(f"Failed to log delivery to Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging delivery to Notion: {e}")
            return False
    
    def log_client_addition(self, client_data: Dict[str, Any]) -> bool:
        """Log new client addition to Notion"""
        if not self.notion_token or not self.database_id:
            logger.warning("Notion credentials not configured")
            return False
        
        try:
            properties = {
                'Client Name': {
                    'title': [
                        {
                            'text': {
                                'content': f"New Client: {client_data['name']}"
                            }
                        }
                    ]
                },
                'Plan': {
                    'rich_text': [
                        {
                            'text': {
                                'content': client_data['plan'].capitalize()
                            }
                        }
                    ]
                },
                'Lead Count Quota': {
                    'number': client_data['lead_count']
                },
                'Monthly Revenue': {
                    'number': client_data.get('monthly_revenue', 0)
                },
                'Exclusive': {
                    'checkbox': client_data.get('exclusive', False)
                },
                'Status': {
                    'select': {
                        'name': 'New Client'
                    }
                },
                'Date Added': {
                    'date': {
                        'start': client_data['created_at']
                    }
                }
            }
            
            url = f'{self.base_url}/pages'
            data = {
                'parent': {'database_id': self.database_id},
                'properties': properties
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Successfully logged new client to Notion: {client_data['name']}")
                return True
            else:
                logger.error(f"Failed to log client to Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging client to Notion: {e}")
            return False
    
    def log_lead_upload(self, upload_data: Dict[str, Any]) -> bool:
        """Log lead upload to Notion"""
        if not self.notion_token or not self.database_id:
            logger.warning("Notion credentials not configured")
            return False
        
        try:
            properties = {
                'Client Name': {
                    'title': [
                        {
                            'text': {
                                'content': f"Lead Upload: {upload_data['filename']}"
                            }
                        }
                    ]
                },
                'Leads Count': {
                    'number': upload_data['leads_processed']
                },
                'Duplicates Removed': {
                    'number': upload_data['duplicates_removed']
                },
                'Status': {
                    'select': {
                        'name': 'Leads Uploaded'
                    }
                },
                'Upload Date': {
                    'date': {
                        'start': upload_data['timestamp']
                    }
                }
            }
            
            url = f'{self.base_url}/pages'
            data = {
                'parent': {'database_id': self.database_id},
                'properties': properties
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Successfully logged lead upload to Notion")
                return True
            else:
                logger.error(f"Failed to log upload to Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging upload to Notion: {e}")
            return False
    
    def get_recent_deliveries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent deliveries from Notion database"""
        if not self.notion_token or not self.database_id:
            return []
        
        try:
            url = f'{self.base_url}/databases/{self.database_id}/query'
            data = {
                'sorts': [
                    {
                        'property': 'Delivery Date',
                        'direction': 'descending'
                    }
                ],
                'page_size': limit
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                deliveries = []
                
                for result in results:
                    props = result.get('properties', {})
                    delivery = {
                        'id': result.get('id', ''),
                        'client_name': self._extract_title(props.get('Client Name', {})),
                        'leads_count': self._extract_number(props.get('Leads Count', {})),
                        'status': self._extract_select(props.get('Status', {})),
                        'delivery_date': self._extract_date(props.get('Delivery Date', {})),
                        'google_drive_url': self._extract_url(props.get('Google Drive URL', {}))
                    }
                    deliveries.append(delivery)
                
                return deliveries
            else:
                logger.error(f"Failed to get deliveries from Notion: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting deliveries from Notion: {e}")
            return []
    
    def get_all_deliveries(self) -> List[Dict[str, Any]]:
        """Get all deliveries from Notion database"""
        return self.get_recent_deliveries(limit=100)  # Increase limit for all deliveries
    
    def update_delivery_status(self, page_id: str, status: str) -> bool:
        """Update delivery status in Notion"""
        if not self.notion_token:
            return False
        
        try:
            url = f'{self.base_url}/pages/{page_id}'
            data = {
                'properties': {
                    'Status': {
                        'select': {
                            'name': status
                        }
                    }
                }
            }
            
            response = requests.patch(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Successfully updated delivery status to {status}")
                return True
            else:
                logger.error(f"Failed to update delivery status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating delivery status: {e}")
            return False
    
    def _extract_title(self, prop: Dict) -> str:
        """Extract title from Notion property"""
        try:
            return prop.get('title', [{}])[0].get('text', {}).get('content', '')
        except:
            return ''
    
    def _extract_number(self, prop: Dict) -> int:
        """Extract number from Notion property"""
        try:
            return prop.get('number', 0) or 0
        except:
            return 0
    
    def _extract_select(self, prop: Dict) -> str:
        """Extract select value from Notion property"""
        try:
            return prop.get('select', {}).get('name', '')
        except:
            return ''
    
    def _extract_date(self, prop: Dict) -> str:
        """Extract date from Notion property"""
        try:
            return prop.get('date', {}).get('start', '')
        except:
            return ''
    
    def _extract_url(self, prop: Dict) -> str:
        """Extract URL from Notion property"""
        try:
            return prop.get('url', '')
        except:
            return ''
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for Notion API"""
        try:
            if not date_str:
                return datetime.now().isoformat()
            
            # Handle different date formats
            if 'T' in date_str:
                # ISO format
                return date_str.split('T')[0]
            else:
                # Assume it's already in YYYY-MM-DD format
                return date_str
        except:
            return datetime.now().date().isoformat()
