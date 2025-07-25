import os
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Set, List, Dict, Any
import hashlib
from config import Config

logger = logging.getLogger(__name__)

class DeduplicationService:
    """Service for handling lead deduplication across deliveries"""
    
    def __init__(self):
        self.config = Config()
        self.dedup_file = 'data/delivered_leads.json'
        self.exclusive_file = 'data/exclusive_leads.json'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load existing delivered leads
        self.delivered_leads = self._load_delivered_leads()
        self.exclusive_leads = self._load_exclusive_leads()
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates from uploaded lead DataFrame"""
        try:
            logger.info(f"Starting deduplication process for {len(df)} leads")
            
            # Remove internal duplicates (within the same upload)
            original_count = len(df)
            
            # Use email as primary deduplication key
            df_deduplicated = df.drop_duplicates(subset=['email'], keep='first')
            internal_duplicates = original_count - len(df_deduplicated)
            
            # Remove leads that were already delivered (based on deduplication window)
            cutoff_date = datetime.now() - timedelta(days=self.config.DEDUPLICATION_WINDOW_DAYS)
            recent_delivered = {
                email for email, delivery_date in self.delivered_leads.items()
                if datetime.fromisoformat(delivery_date) > cutoff_date
            }
            
            # Filter out recently delivered leads
            mask = ~df_deduplicated['email'].isin(recent_delivered)
            df_final = df_deduplicated[mask]
            
            external_duplicates = len(df_deduplicated) - len(df_final)
            total_removed = internal_duplicates + external_duplicates
            
            logger.info(f"Deduplication completed: removed {total_removed} duplicates ({internal_duplicates} internal, {external_duplicates} external)")
            
            return df_final
            
        except Exception as e:
            logger.error(f"Error in deduplication: {e}")
            return df
    
    def is_lead_delivered(self, email: str) -> bool:
        """Check if a lead was already delivered within the deduplication window"""
        if email not in self.delivered_leads:
            return False
        
        # Check if delivery was within the deduplication window
        delivery_date = datetime.fromisoformat(self.delivered_leads[email])
        cutoff_date = datetime.now() - timedelta(days=self.config.DEDUPLICATION_WINDOW_DAYS)
        
        return delivery_date > cutoff_date
    
    def is_lead_exclusive_delivered(self, email: str) -> bool:
        """Check if a lead was delivered to an exclusive client"""
        return email in self.exclusive_leads
    
    def mark_leads_as_delivered(self, emails: List[str], exclusive: bool = False):
        """Mark leads as delivered to prevent future duplicates"""
        try:
            current_time = datetime.now().isoformat()
            
            # Update delivered leads tracking
            for email in emails:
                self.delivered_leads[email] = current_time
                
                # If exclusive, also mark in exclusive tracking
                if exclusive:
                    self.exclusive_leads[email] = current_time
            
            # Save to files
            self._save_delivered_leads()
            if exclusive:
                self._save_exclusive_leads()
            
            logger.info(f"Marked {len(emails)} leads as delivered (exclusive: {exclusive})")
            
        except Exception as e:
            logger.error(f"Error marking leads as delivered: {e}")
    
    def get_lead_fingerprint(self, lead_data: Dict[str, Any]) -> str:
        """Generate unique fingerprint for a lead"""
        # Create fingerprint based on email + company combination
        fingerprint_data = f"{lead_data.get('email', '').lower()}_{lead_data.get('company', '').lower()}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    def clean_old_records(self):
        """Clean up old deduplication records beyond the window"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.DEDUPLICATION_WINDOW_DAYS * 2)  # Keep extra buffer
            
            # Clean delivered leads
            old_count = len(self.delivered_leads)
            self.delivered_leads = {
                email: date for email, date in self.delivered_leads.items()
                if datetime.fromisoformat(date) > cutoff_date
            }
            
            # Clean exclusive leads (keep them longer - exclusive status is important)
            exclusive_cutoff = datetime.now() - timedelta(days=90)  # Keep exclusive records for 90 days
            self.exclusive_leads = {
                email: date for email, date in self.exclusive_leads.items()
                if datetime.fromisoformat(date) > exclusive_cutoff
            }
            
            removed_count = old_count - len(self.delivered_leads)
            
            # Save cleaned data
            self._save_delivered_leads()
            self._save_exclusive_leads()
            
            logger.info(f"Cleaned {removed_count} old deduplication records")
            
        except Exception as e:
            logger.error(f"Error cleaning old records: {e}")
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.DEDUPLICATION_WINDOW_DAYS)
            
            recent_delivered = sum(
                1 for date in self.delivered_leads.values()
                if datetime.fromisoformat(date) > cutoff_date
            )
            
            exclusive_count = len(self.exclusive_leads)
            total_tracked = len(self.delivered_leads)
            
            return {
                'total_tracked_leads': total_tracked,
                'recent_delivered_leads': recent_delivered,
                'exclusive_delivered_leads': exclusive_count,
                'deduplication_window_days': self.config.DEDUPLICATION_WINDOW_DAYS,
                'last_cleanup': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting deduplication stats: {e}")
            return {}
    
    def _load_delivered_leads(self) -> Dict[str, str]:
        """Load delivered leads from file"""
        try:
            if os.path.exists(self.dedup_file):
                with open(self.dedup_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading delivered leads: {e}")
            return {}
    
    def _load_exclusive_leads(self) -> Dict[str, str]:
        """Load exclusive leads from file"""
        try:
            if os.path.exists(self.exclusive_file):
                with open(self.exclusive_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading exclusive leads: {e}")
            return {}
    
    def _save_delivered_leads(self):
        """Save delivered leads to file"""
        try:
            with open(self.dedup_file, 'w') as f:
                json.dump(self.delivered_leads, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving delivered leads: {e}")
    
    def _save_exclusive_leads(self):
        """Save exclusive leads to file"""
        try:
            with open(self.exclusive_file, 'w') as f:
                json.dump(self.exclusive_leads, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving exclusive leads: {e}")
