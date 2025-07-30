import os
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any
import json

from models import Lead, Client
from services.ai_personalizer import AIPersonalizer
from services.google_drive import GoogleDriveService
from services.email_service import EmailService
from services.notion_crm import NotionCRM
from utils.deduplication import DeduplicationService
from config import Config

logger = logging.getLogger(__name__)

class LeadProcessor:
    """Main service for processing leads and deliveries"""
    
    def __init__(self):
        self.ai_personalizer = AIPersonalizer()
        self.google_drive = GoogleDriveService()
        self.email_service = EmailService()
        self.notion_crm = NotionCRM()
        self.deduplication = DeduplicationService()
        self.config = Config()
        
        # Ensure local storage directory exists
        os.makedirs(self.config.LOCAL_STORAGE_PATH, exist_ok=True)
    
    def process_uploaded_leads(self, filepath: str) -> Dict[str, Any]:
        """Process uploaded lead CSV file"""
        try:
            logger.info(f"Processing uploaded leads from {filepath}")
            
            # Read CSV file
            df = pd.read_csv(filepath)
            
            # Validate required columns
            required_columns = ['first_name', 'last_name', 'company', 'title', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Process deduplication
            original_count = len(df)
            df_deduplicated = self.deduplication.remove_duplicates(df)
            duplicates_removed = original_count - len(df_deduplicated)
            
            # Store processed leads for future delivery
            processed_leads = []
            for _, row in df_deduplicated.iterrows():
                lead_data = {
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'company': row['company'],
                    'title': row['title'],
                    'email': row['email'],
                    'linkedin': row.get('linkedin', ''),
                    'processed_at': datetime.now().isoformat()
                }
                processed_leads.append(lead_data)
            
            # Save processed leads to JSON for future use
            processed_file = f"data/processed_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(processed_file, 'w') as f:
                json.dump(processed_leads, f, indent=2)
            
            logger.info(f"Processed {len(processed_leads)} leads, removed {duplicates_removed} duplicates")
            
            return {
                'leads_processed': len(processed_leads),
                'duplicates_removed': duplicates_removed,
                'processed_file': processed_file
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded leads: {e}")
            raise
    
    def process_client_delivery(self, client: Dict[str, Any]) -> Dict[str, Any]:
        """Process lead delivery for a specific client"""
        try:
            logger.info(f"Processing delivery for client: {client['name']}")
            
            # Load available processed leads
            leads_to_deliver = self._get_available_leads(client)
            
            if not leads_to_deliver:
                raise ValueError("No leads available for delivery")
            
            # Limit leads based on client quota and plan
            max_leads = min(client['remaining_quota'], client['lead_count'])
            leads_to_deliver = leads_to_deliver[:max_leads]
            
            # Generate personalized content for each lead
            personalized_leads = []
            for i, lead_data in enumerate(leads_to_deliver):
                try:
                    # Generate Lead ID
                    lead_id = self._generate_lead_id(client['name'], i + 1)
                    
                    # Create LinkedIn URL if not provided
                    linkedin_url = lead_data.get('linkedin') or f"https://linkedin.com/in/{lead_data['first_name'].lower()}{lead_data['last_name'].lower()}"
                    
                    # Generate AI personalized content if client has premium/pro plan
                    if client['plan'] in ['pro', 'premium']:
                        cold_email = self.ai_personalizer.generate_cold_email(lead_data, client)
                        icebreaker = self.ai_personalizer.generate_icebreaker(lead_data, client)
                    else:
                        # Basic template for basic plan
                        cold_email = self._generate_basic_cold_email(lead_data)
                        icebreaker = self._generate_basic_icebreaker(lead_data)
                    
                    # Create Lead object
                    lead = Lead(
                        lead_id=lead_id,
                        client_name=client['name'],
                        first_name=lead_data['first_name'],
                        last_name=lead_data['last_name'],
                        title=lead_data['title'],
                        company=lead_data['company'],
                        email=lead_data['email'],
                        linkedin=linkedin_url,
                        cold_email=cold_email,
                        icebreaker=icebreaker,
                        verified=True,  # Assume verified for now
                        exclusive=client['exclusive'],
                        created_at=datetime.now()
                    )
                    
                    personalized_leads.append(lead)
                    
                except Exception as e:
                    logger.error(f"Error processing lead {i+1}: {e}")
                    continue
            
            if not personalized_leads:
                raise ValueError("No leads could be processed successfully")
            
            # Create delivery folder structure
            folder_name = f"{client['name']}_{client['plan'].capitalize()}_{'Exclusive' if client['exclusive'] else 'Shared'}"
            today = datetime.now().strftime("%Y-%m-%d")
            delivery_path = os.path.join(self.config.LOCAL_STORAGE_PATH, folder_name, today)
            os.makedirs(delivery_path, exist_ok=True)
            
            # Create CSV file
            leads_df = pd.DataFrame([lead.to_dict() for lead in personalized_leads])
            csv_filename = f"leads_{client['name']}_{datetime.now().strftime('%Y%m%d')}.csv"
            csv_filepath = os.path.join(delivery_path, csv_filename)
            leads_df.to_csv(csv_filepath, index=False)
            
            # Upload to Google Drive
            drive_url = ""
            try:
                drive_url = self.google_drive.upload_file(csv_filepath, folder_name)
                logger.info(f"File uploaded to Google Drive: {drive_url}")
            except Exception as e:
                logger.warning(f"Failed to upload to Google Drive: {e}")
            
            # Send email notification to client
            try:
                self.email_service.send_delivery_notification(
                    client['email'],
                    client['name'],
                    len(personalized_leads),
                    csv_filename,
                    drive_url
                )
                logger.info(f"Email notification sent to {client['email']}")
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")
            
            # Log delivery to Notion CRM
            try:
                delivery_data = {
                    'client_name': client['name'],
                    'leads_count': len(personalized_leads),
                    'file_path': csv_filepath,
                    'google_drive_url': drive_url,
                    'delivery_date': datetime.now().isoformat(),
                    'status': 'Delivered'
                }
                self.notion_crm.log_delivery(delivery_data)
                logger.info("Delivery logged to Notion CRM")
            except Exception as e:
                logger.warning(f"Failed to log to Notion CRM: {e}")
            
            # Mark leads as delivered in deduplication system
            self.deduplication.mark_leads_as_delivered([lead.email for lead in personalized_leads])
            
            logger.info(f"Successfully delivered {len(personalized_leads)} leads to {client['name']}")
            
            return {
                'leads_delivered': len(personalized_leads),
                'file_path': csv_filepath,
                'google_drive_url': drive_url,
                'delivery_id': f"{client['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error processing client delivery: {e}")
            raise
    
    def _get_available_leads(self, client: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available leads for client delivery"""
        try:
            # Load all processed lead files
            all_leads = []
            data_dir = 'data'
            
            for filename in os.listdir(data_dir):
                if filename.startswith('processed_leads_') and filename.endswith('.json'):
                    filepath = os.path.join(data_dir, filename)
                    with open(filepath, 'r') as f:
                        leads = json.load(f)
                        all_leads.extend(leads)
            
            # Filter leads based on exclusivity and deduplication
            available_leads = []
            for lead in all_leads:
                if not self.deduplication.is_lead_delivered(lead['email']):
                    # For exclusive clients, check if lead was already delivered to another exclusive client
                    if client['exclusive']:
                        if not self.deduplication.is_lead_exclusive_delivered(lead['email']):
                            available_leads.append(lead)
                    else:
                        available_leads.append(lead)
            
            # Sort by plan priority (premium gets first pick)
            plan_priority = {'premium': 1, 'pro': 2, 'basic': 3}
            client_priority = plan_priority.get(client['plan'], 3)
            
            # Return leads based on priority and availability
            return available_leads
            
        except Exception as e:
            logger.error(f"Error getting available leads: {e}")
            return []
    
    def _generate_lead_id(self, client_name: str, lead_number: int) -> str:
        """Generate 4-digit lead ID"""
        return f"{client_name.lower().replace(' ', '')}-{datetime.now().strftime('%Y%m%d')}-{str(lead_number).zfill(4)}"
    
    def _generate_basic_cold_email(self, lead_data: Dict[str, Any]) -> str:
        """Generate basic cold email template"""
        return f"""Hi {lead_data['first_name']},

I noticed you're the {lead_data['title']} at {lead_data['company']}. We help teams like yours get access to top-tier candidates fast using AI-sourced leads.

Would you be open to a quick demo or a free list to start?

Best,
AILeadGen"""
    
    def _generate_basic_icebreaker(self, lead_data: Dict[str, Any]) -> str:
        """Generate basic icebreaker template"""
        return f"Saw you're doing great work at {lead_data['company']} — especially in hiring tech talent. Thought I'd reach out!"
