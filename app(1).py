import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from database import db
from services.lead_processor import LeadProcessor
from services.scheduler import SchedulerService
from services.notion_crm import NotionCRM
from utils.validators import validate_csv_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
try:
    db.init_database()
    # Migrate existing data if present
    db.migrate_from_files()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Initialize services
lead_processor = LeadProcessor()
scheduler_service = SchedulerService()
notion_crm = NotionCRM()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

@app.route('/')
def index():
    """Dashboard showing system overview"""
    try:
        # Get statistics from database
        stats = db.get_stats()
        
        # Get recent clients and deliveries
        clients = db.get_active_clients()[:5]  # Show first 5 active clients
        recent_deliveries = db.get_recent_deliveries(10)
        
        # Update stats format for template compatibility
        stats['active_deliveries'] = stats.get('total_deliveries', 0)
        stats['pending_leads'] = stats.get('remaining_quota', 0)
        stats['total_revenue'] = stats.get('monthly_revenue', 0)
        
        return render_template('index.html', stats=stats, recent_deliveries=recent_deliveries, clients=clients)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', stats={}, recent_deliveries=[], clients=[])

@app.route('/upload')
def upload_page():
    """Lead upload page"""
    try:
        clients = db.get_active_clients()
        return render_template('upload.html', clients=clients)
    except Exception as e:
        logger.error(f"Error loading upload page: {e}")
        return render_template('upload.html', clients=[])

@app.route('/upload_leads', methods=['POST'])
def upload_leads():
    """Handle lead file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not validate_csv_file(file):
            return jsonify({'error': 'Invalid CSV file format'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process leads
        result = lead_processor.process_uploaded_leads(filepath)
        
        # Log to Notion
        notion_crm.log_lead_upload({
            'filename': filename,
            'leads_processed': result['leads_processed'],
            'duplicates_removed': result['duplicates_removed'],
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': f"Processed {result['leads_processed']} leads, removed {result['duplicates_removed']} duplicates",
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error uploading leads: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clients')
def clients_page():
    """Client management page"""
    try:
        clients = db.get_all_clients()
        return render_template('clients.html', clients=clients)
    except Exception as e:
        logger.error(f"Error loading clients page: {e}")
        return render_template('clients.html', clients=[])

@app.route('/add_client', methods=['POST'])
def add_client():
    """Add new client"""
    try:
        data = request.get_json()
        
        # Create new client data
        new_client = {
            'name': data['name'],
            'plan': data['plan'],
            'exclusive': data.get('exclusive', False),
            'lead_count': int(data['lead_count']),
            'email': data['email'],
            'monthly_revenue': float(data.get('monthly_revenue', 0)),
            'remaining_quota': int(data['lead_count']),
            'active': True
        }
        
        # Insert into database
        client_id = db.insert_client(new_client)
        new_client['id'] = client_id
        new_client['created_at'] = datetime.now().isoformat()
        
        # Log to Notion
        notion_crm.log_client_addition(new_client)
        
        return jsonify({'success': True, 'client': new_client})
        
    except Exception as e:
        logger.error(f"Error adding client: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/deliveries')
def deliveries_page():
    """Delivery tracking page"""
    try:
        deliveries = db.get_all_deliveries()
        return render_template('deliveries.html', deliveries=deliveries)
    except Exception as e:
        logger.error(f"Error loading deliveries page: {e}")
        return render_template('deliveries.html', deliveries=[])

@app.route('/process_delivery/<int:client_id>')
def process_delivery(client_id):
    """Process lead delivery for a specific client"""
    try:
        # Get client data from database
        client = db.get_client_by_id(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Process delivery
        result = lead_processor.process_client_delivery(client)
        
        # Update client quota in database
        new_quota = max(0, client['remaining_quota'] - result['leads_delivered'])
        db.update_client_quota(client_id, new_quota)
        
        return jsonify({
            'success': True,
            'message': f"Delivered {result['leads_delivered']} leads to {client['name']}",
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error processing delivery for client {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/schedule_automation', methods=['POST'])
def schedule_automation():
    """Configure automated scheduling"""
    try:
        data = request.get_json()
        schedule_time = data.get('schedule_time', '09:00')
        enabled = data.get('enabled', True)
        
        if enabled:
            scheduler_service.schedule_daily_processing(schedule_time)
            message = f"Automation scheduled for {schedule_time} daily"
        else:
            scheduler_service.stop_scheduling()
            message = "Automation stopped"
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        logger.error(f"Error configuring automation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time stats"""
    try:
        stats = db.get_stats()
        recent_deliveries = db.get_recent_deliveries(5)
        
        # Add additional stats for API compatibility
        stats['total_quota'] = stats.get('remaining_quota', 0)
        stats['recent_deliveries_count'] = len(recent_deliveries)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('index.html'), 500

if __name__ == '__main__':
    # Start scheduler in background
    scheduler_service.start()
    
    # Run Flask app
    import os
port = int(os.environ.get("PORT", 10000))  # Use Railway's assigned port or default 10000
app.run(host="0.0.0.0", port=port)

# Run Flask app on Railway-compatible settings
port = int(os.environ.get("PORT", 10000))

