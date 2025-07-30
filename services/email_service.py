import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional
from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.config = Config()
        self.smtp_server = self.config.SMTP_SERVER
        self.smtp_port = self.config.SMTP_PORT
        self.email_user = os.environ.get('EMAIL_USER', '')
        self.email_password = os.environ.get('EMAIL_PASSWORD', '')
        self.from_email = self.config.FROM_EMAIL
    
    def send_delivery_notification(self, to_email: str, client_name: str, 
                                 leads_count: int, filename: str, 
                                 drive_url: str = '') -> bool:
        """Send delivery notification to client"""
        try:
            subject = f"Your {leads_count} Fresh Leads Are Ready! 🎯"
            
            # Create HTML email content
            html_content = self._create_delivery_email_html(
                client_name, leads_count, filename, drive_url
            )
            
            # Create text version
            text_content = self._create_delivery_email_text(
                client_name, leads_count, filename, drive_url
            )
            
            return self._send_email(to_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending delivery notification: {e}")
            return False
    
    def send_commission_reminder(self, to_email: str, commission_data: dict) -> bool:
        """Send commission reminder email"""
        try:
            subject = f"Commission Payment Due - ${commission_data['amount']:.2f}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Commission Payment Reminder</h2>
                <p>Hello,</p>
                <p>This is a reminder that you have a commission payment due:</p>
                <ul>
                    <li><strong>Client:</strong> {commission_data['client_name']}</li>
                    <li><strong>Period:</strong> {commission_data['period']}</li>
                    <li><strong>Commission Amount:</strong> ${commission_data['commission_amount']:.2f}</li>
                    <li><strong>Due Date:</strong> {commission_data['due_date']}</li>
                </ul>
                <p>Please process this payment at your earliest convenience.</p>
                <p>Best regards,<br>AILeadGen System</p>
            </body>
            </html>
            """
            
            text_content = f"""
Commission Payment Reminder

Hello,

This is a reminder that you have a commission payment due:

Client: {commission_data['client_name']}
Period: {commission_data['period']}
Commission Amount: ${commission_data['commission_amount']:.2f}
Due Date: {commission_data['due_date']}

Please process this payment at your earliest convenience.

Best regards,
AILeadGen System
            """
            
            return self._send_email(to_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending commission reminder: {e}")
            return False
    
    def send_system_alert(self, to_emails: List[str], alert_type: str, message: str) -> bool:
        """Send system alert email"""
        try:
            subject = f"AILeadGen System Alert - {alert_type}"
            
            html_content = f"""
            <html>
            <body>
                <h2>System Alert: {alert_type}</h2>
                <p><strong>Alert Details:</strong></p>
                <p>{message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Please investigate and take appropriate action.</p>
                <p>Best regards,<br>AILeadGen Monitoring System</p>
            </body>
            </html>
            """
            
            text_content = f"""
System Alert: {alert_type}

Alert Details:
{message}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please investigate and take appropriate action.

Best regards,
AILeadGen Monitoring System
            """
            
            # Send to all recipients
            success_count = 0
            for email in to_emails:
                if self._send_email(email, subject, html_content, text_content):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str, attachment_path: Optional[str] = None) -> bool:
        """Send email with both HTML and text content"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def _create_delivery_email_html(self, client_name: str, leads_count: int, 
                                  filename: str, drive_url: str) -> str:
        """Create HTML email content for delivery notification"""
        drive_link = f'<p><a href="{drive_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download from Google Drive</a></p>' if drive_url else ''
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h1 style="color: #28a745;">🎯 Your Fresh Leads Are Ready!</h1>
                
                <p>Hi {client_name},</p>
                
                <p>Great news! We've just delivered <strong>{leads_count} high-quality leads</strong> to your account.</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Delivery Summary:</h3>
                    <ul>
                        <li><strong>Leads Count:</strong> {leads_count}</li>
                        <li><strong>File Name:</strong> {filename}</li>
                        <li><strong>Format:</strong> CSV with personalized emails & icebreakers</li>
                        <li><strong>Delivery Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
                    </ul>
                </div>
                
                {drive_link}
                
                <h3>What's Included:</h3>
                <ul>
                    <li>✅ Verified contact information</li>
                    <li>✅ LinkedIn profiles</li>
                    <li>✅ Personalized cold email templates</li>
                    <li>✅ Custom icebreaker messages</li>
                    <li>✅ Company and title details</li>
                </ul>
                
                <p><strong>Pro Tip:</strong> These leads are fresh and ready to contact. For best results, reach out within 24-48 hours!</p>
                
                <p>Questions or need more leads? Just reply to this email!</p>
                
                <p>Best regards,<br>
                <strong>The AILeadGen Team</strong><br>
                🚀 Powering your growth with AI-sourced leads</p>
            </div>
        </body>
        </html>
        """
    
    def _create_delivery_email_text(self, client_name: str, leads_count: int, 
                                   filename: str, drive_url: str) -> str:
        """Create text email content for delivery notification"""
        drive_text = f'\nDownload Link: {drive_url}\n' if drive_url else ''
        
        return f"""
🎯 Your Fresh Leads Are Ready!

Hi {client_name},

Great news! We've just delivered {leads_count} high-quality leads to your account.

Delivery Summary:
- Leads Count: {leads_count}
- File Name: {filename}
- Format: CSV with personalized emails & icebreakers
- Delivery Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{drive_text}
What's Included:
✅ Verified contact information
✅ LinkedIn profiles
✅ Personalized cold email templates
✅ Custom icebreaker messages
✅ Company and title details

Pro Tip: These leads are fresh and ready to contact. For best results, reach out within 24-48 hours!

Questions or need more leads? Just reply to this email!

Best regards,
The AILeadGen Team
🚀 Powering your growth with AI-sourced leads
        """
