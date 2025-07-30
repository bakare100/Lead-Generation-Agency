import schedule
import time
import threading
import logging
from datetime import datetime
import json
import os
from typing import Dict, Any

from services.lead_processor import LeadProcessor
from services.email_service import EmailService
from config import Config

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for automated scheduling and task execution"""
    
    def __init__(self):
        self.config = Config()
        self.lead_processor = LeadProcessor()
        self.email_service = EmailService()
        self.is_running = False
        self.scheduler_thread = None
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def schedule_daily_processing(self, time_str: str = "09:00"):
        """Schedule daily lead processing"""
        try:
            schedule.clear()  # Clear existing schedules
            schedule.every().day.at(time_str).do(self._daily_processing_job)
            logger.info(f"Daily processing scheduled for {time_str}")
        except Exception as e:
            logger.error(f"Error scheduling daily processing: {e}")
    
    def schedule_weekly_commission_reminders(self, day: str = "monday", time_str: str = "10:00"):
        """Schedule weekly commission reminders"""
        try:
            getattr(schedule.every(), day.lower()).at(time_str).do(self._commission_reminder_job)
            logger.info(f"Commission reminders scheduled for {day} at {time_str}")
        except Exception as e:
            logger.error(f"Error scheduling commission reminders: {e}")
    
    def schedule_quota_monitoring(self, time_str: str = "08:00"):
        """Schedule daily quota monitoring"""
        try:
            schedule.every().day.at(time_str).do(self._quota_monitoring_job)
            logger.info(f"Quota monitoring scheduled for {time_str}")
        except Exception as e:
            logger.error(f"Error scheduling quota monitoring: {e}")
    
    def stop_scheduling(self):
        """Stop all scheduled tasks"""
        schedule.clear()
        logger.info("All scheduled tasks cleared")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _daily_processing_job(self):
        """Daily automated processing job"""
        try:
            logger.info("Starting daily processing job")
            
            # Load client data
            try:
                with open('data/clients.json', 'r') as f:
                    clients = json.load(f)
            except FileNotFoundError:
                logger.warning("No clients found for processing")
                return
            
            # Process deliveries for clients with remaining quota
            processed_count = 0
            for client in clients:
                if client.get('active', True) and client.get('remaining_quota', 0) > 0:
                    try:
                        result = self.lead_processor.process_client_delivery(client)
                        
                        # Update client quota
                        client['remaining_quota'] = max(0, client['remaining_quota'] - result['leads_delivered'])
                        processed_count += 1
                        
                        logger.info(f"Processed delivery for {client['name']}: {result['leads_delivered']} leads")
                        
                    except Exception as e:
                        logger.error(f"Error processing delivery for {client['name']}: {e}")
                        continue
            
            # Save updated client data
            if processed_count > 0:
                with open('data/clients.json', 'w') as f:
                    json.dump(clients, f, indent=2)
                
                # Send summary email
                self._send_processing_summary(processed_count)
            
            logger.info(f"Daily processing completed. Processed {processed_count} clients")
            
        except Exception as e:
            logger.error(f"Error in daily processing job: {e}")
    
    def _commission_reminder_job(self):
        """Weekly commission reminder job"""
        try:
            logger.info("Starting commission reminder job")
            
            # Load client data
            try:
                with open('data/clients.json', 'r') as f:
                    clients = json.load(f)
            except FileNotFoundError:
                logger.warning("No clients found for commission reminders")
                return
            
            # Calculate commissions and send reminders
            for client in clients:
                if client.get('active', True) and client.get('monthly_revenue', 0) > 0:
                    commission_rate = self.config.COMMISSION_RATES.get(client['plan'], 0.10)
                    commission_amount = client['monthly_revenue'] * commission_rate
                    
                    commission_data = {
                        'client_name': client['name'],
                        'period': datetime.now().strftime('%Y-%m'),
                        'amount': client['monthly_revenue'],
                        'commission_amount': commission_amount,
                        'due_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    # Send reminder email (to admin/commission recipient)
                    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@aileadgen.com')
                    self.email_service.send_commission_reminder(admin_email, commission_data)
            
            logger.info("Commission reminder job completed")
            
        except Exception as e:
            logger.error(f"Error in commission reminder job: {e}")
    
    def _quota_monitoring_job(self):
        """Daily quota monitoring job"""
        try:
            logger.info("Starting quota monitoring job")
            
            # Load client data
            try:
                with open('data/clients.json', 'r') as f:
                    clients = json.load(f)
            except FileNotFoundError:
                logger.warning("No clients found for quota monitoring")
                return
            
            # Check for low quotas and inactive clients
            low_quota_clients = []
            inactive_clients = []
            
            for client in clients:
                if client.get('active', True):
                    remaining = client.get('remaining_quota', 0)
                    total = client.get('lead_count', 0)
                    
                    # Alert if quota is below 20%
                    if total > 0 and (remaining / total) < 0.2:
                        low_quota_clients.append(client)
                    
                    # Alert if no quota remaining
                    if remaining <= 0:
                        inactive_clients.append(client)
            
            # Send alerts if needed
            if low_quota_clients or inactive_clients:
                self._send_quota_alerts(low_quota_clients, inactive_clients)
            
            logger.info(f"Quota monitoring completed. Found {len(low_quota_clients)} low quota and {len(inactive_clients)} depleted clients")
            
        except Exception as e:
            logger.error(f"Error in quota monitoring job: {e}")
    
    def _send_processing_summary(self, processed_count: int):
        """Send daily processing summary email"""
        try:
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@aileadgen.com')
            subject = f"Daily Processing Summary - {processed_count} Clients Processed"
            
            message = f"""
Daily Processing Summary for {datetime.now().strftime('%Y-%m-%d')}

Successfully processed deliveries for {processed_count} clients.

All deliveries have been:
- Generated with AI personalization
- Uploaded to Google Drive
- Email notifications sent to clients
- Logged to Notion CRM

System is running smoothly.
            """
            
            self.email_service.send_system_alert([admin_email], "Daily Summary", message)
            
        except Exception as e:
            logger.error(f"Error sending processing summary: {e}")
    
    def _send_quota_alerts(self, low_quota_clients: list, inactive_clients: list):
        """Send quota alert emails"""
        try:
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@aileadgen.com')
            
            alert_message = "Quota Alert Summary:\n\n"
            
            if low_quota_clients:
                alert_message += "Clients with Low Quota (< 20% remaining):\n"
                for client in low_quota_clients:
                    remaining = client.get('remaining_quota', 0)
                    total = client.get('lead_count', 0)
                    percentage = (remaining / total) * 100 if total > 0 else 0
                    alert_message += f"- {client['name']}: {remaining}/{total} ({percentage:.1f}%)\n"
                alert_message += "\n"
            
            if inactive_clients:
                alert_message += "Clients with Depleted Quota:\n"
                for client in inactive_clients:
                    alert_message += f"- {client['name']}: {client['plan']} plan\n"
                alert_message += "\n"
            
            alert_message += "Consider reaching out to these clients for quota renewal."
            
            self.email_service.send_system_alert([admin_email], "Quota Alert", alert_message)
            
        except Exception as e:
            logger.error(f"Error sending quota alerts: {e}")
    
    def run_manual_processing(self, client_id: int = None):
        """Run manual processing for specific client or all clients"""
        try:
            logger.info(f"Starting manual processing for client {client_id if client_id else 'all'}")
            
            with open('data/clients.json', 'r') as f:
                clients = json.load(f)
            
            if client_id:
                # Process specific client
                client = next((c for c in clients if c['id'] == client_id), None)
                if not client:
                    raise ValueError(f"Client {client_id} not found")
                
                result = self.lead_processor.process_client_delivery(client)
                return result
            else:
                # Process all active clients
                results = []
                for client in clients:
                    if client.get('active', True) and client.get('remaining_quota', 0) > 0:
                        try:
                            result = self.lead_processor.process_client_delivery(client)
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Error processing client {client['name']}: {e}")
                            continue
                
                return results
                
        except Exception as e:
            logger.error(f"Error in manual processing: {e}")
            raise
