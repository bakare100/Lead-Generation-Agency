import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for PostgreSQL operations"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create clients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    plan VARCHAR(50) NOT NULL,
                    exclusive BOOLEAN DEFAULT FALSE,
                    lead_count INTEGER DEFAULT 0,
                    email VARCHAR(255) NOT NULL,
                    monthly_revenue DECIMAL(10,2) DEFAULT 0.00,
                    remaining_quota INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create leads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    lead_id VARCHAR(50) UNIQUE NOT NULL,
                    client_name VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    title VARCHAR(255),
                    company VARCHAR(255),
                    email VARCHAR(255) NOT NULL,
                    linkedin VARCHAR(500),
                    cold_email TEXT,
                    icebreaker TEXT,
                    verified BOOLEAN DEFAULT FALSE,
                    exclusive BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP
                )
            """)
            
            # Create deliveries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id SERIAL PRIMARY KEY,
                    delivery_id VARCHAR(50) UNIQUE NOT NULL,
                    client_id INTEGER REFERENCES clients(id),
                    client_name VARCHAR(255),
                    leads_count INTEGER,
                    file_path VARCHAR(500),
                    google_drive_url VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP
                )
            """)
            
            # Create commission_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_records (
                    id SERIAL PRIMARY KEY,
                    record_id VARCHAR(50) UNIQUE NOT NULL,
                    client_id INTEGER REFERENCES clients(id),
                    client_name VARCHAR(255),
                    amount DECIMAL(10,2),
                    commission_rate DECIMAL(5,4),
                    commission_amount DECIMAL(10,2),
                    period VARCHAR(20),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP
                )
            """)
            
            # Create deduplication table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivered_leads (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    fingerprint VARCHAR(255) NOT NULL,
                    exclusive BOOLEAN DEFAULT FALSE,
                    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, fingerprint)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_delivered_at ON leads(delivered_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_delivered_leads_email ON delivered_leads(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_delivered_leads_delivered_at ON delivered_leads(delivered_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status)")
            
            conn.commit()
            logger.info("Database tables initialized successfully")
    
    def insert_client(self, client_data: Dict[str, Any]) -> int:
        """Insert new client and return ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, plan, exclusive, lead_count, email, monthly_revenue, remaining_quota, active)
                VALUES (%(name)s, %(plan)s, %(exclusive)s, %(lead_count)s, %(email)s, %(monthly_revenue)s, %(remaining_quota)s, %(active)s)
                RETURNING id
            """, client_data)
            client_id = cursor.fetchone()[0]
            conn.commit()
            return client_id
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get all clients"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM clients ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_clients(self) -> List[Dict[str, Any]]:
        """Get all active clients"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM clients WHERE active = TRUE ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_client_quota(self, client_id: int, remaining_quota: int):
        """Update client remaining quota"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clients SET remaining_quota = %s WHERE id = %s
            """, (remaining_quota, client_id))
            conn.commit()
    
    def insert_leads(self, leads: List[Dict[str, Any]]):
        """Insert multiple leads"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for lead in leads:
                cursor.execute("""
                    INSERT INTO leads (lead_id, client_name, first_name, last_name, title, company, email, linkedin, cold_email, icebreaker, verified, exclusive, delivered_at)
                    VALUES (%(lead_id)s, %(client_name)s, %(first_name)s, %(last_name)s, %(title)s, %(company)s, %(email)s, %(linkedin)s, %(cold_email)s, %(icebreaker)s, %(verified)s, %(exclusive)s, %(delivered_at)s)
                    ON CONFLICT (lead_id) DO NOTHING
                """, lead)
            conn.commit()
    
    def get_available_leads(self, exclude_delivered: bool = True) -> List[Dict[str, Any]]:
        """Get available leads for delivery"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if exclude_delivered:
                cursor.execute("SELECT * FROM leads WHERE delivered_at IS NULL ORDER BY created_at ASC")
            else:
                cursor.execute("SELECT * FROM leads ORDER BY created_at ASC")
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_leads_delivered(self, lead_ids: List[str], delivered_at: datetime = None):
        """Mark leads as delivered"""
        if not delivered_at:
            delivered_at = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leads SET delivered_at = %s WHERE lead_id = ANY(%s)
            """, (delivered_at, lead_ids))
            conn.commit()
    
    def insert_delivery(self, delivery_data: Dict[str, Any]) -> str:
        """Insert delivery record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deliveries (delivery_id, client_id, client_name, leads_count, file_path, google_drive_url, status, delivered_at)
                VALUES (%(delivery_id)s, %(client_id)s, %(client_name)s, %(leads_count)s, %(file_path)s, %(google_drive_url)s, %(status)s, %(delivered_at)s)
                RETURNING delivery_id
            """, delivery_data)
            delivery_id = cursor.fetchone()[0]
            conn.commit()
            return delivery_id
    
    def get_all_deliveries(self) -> List[Dict[str, Any]]:
        """Get all deliveries"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM deliveries ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_deliveries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent deliveries"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM deliveries ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_delivery_status(self, delivery_id: str, status: str):
        """Update delivery status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE deliveries SET status = %s WHERE delivery_id = %s
            """, (status, delivery_id))
            conn.commit()
    
    def check_lead_delivered(self, email: str) -> bool:
        """Check if lead was already delivered"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM delivered_leads WHERE email = %s", (email,))
            return cursor.fetchone() is not None
    
    def check_lead_exclusive_delivered(self, email: str) -> bool:
        """Check if lead was delivered to exclusive client"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM delivered_leads WHERE email = %s AND exclusive = TRUE", (email,))
            return cursor.fetchone() is not None
    
    def mark_lead_delivered(self, email: str, fingerprint: str, exclusive: bool = False):
        """Mark lead as delivered for deduplication"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO delivered_leads (email, fingerprint, exclusive)
                VALUES (%s, %s, %s)
                ON CONFLICT (email, fingerprint) DO NOTHING
            """, (email, fingerprint, exclusive))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            total_clients = cursor.fetchone()[0]
            
            # Active clients
            cursor.execute("SELECT COUNT(*) FROM clients WHERE active = TRUE")
            active_clients = cursor.fetchone()[0]
            
            # Total remaining quota
            cursor.execute("SELECT COALESCE(SUM(remaining_quota), 0) FROM clients WHERE active = TRUE")
            remaining_quota = cursor.fetchone()[0]
            
            # Monthly revenue
            cursor.execute("SELECT COALESCE(SUM(monthly_revenue), 0) FROM clients WHERE active = TRUE")
            monthly_revenue = cursor.fetchone()[0]
            
            # Total leads
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            
            # Delivered leads
            cursor.execute("SELECT COUNT(*) FROM leads WHERE delivered_at IS NOT NULL")
            delivered_leads = cursor.fetchone()[0]
            
            # Total deliveries
            cursor.execute("SELECT COUNT(*) FROM deliveries")
            total_deliveries = cursor.fetchone()[0]
            
            return {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'remaining_quota': remaining_quota,
                'monthly_revenue': float(monthly_revenue),
                'total_leads': total_leads,
                'delivered_leads': delivered_leads,
                'total_deliveries': total_deliveries
            }
    
    def migrate_from_files(self):
        """Migrate existing data from JSON files to database"""
        try:
            # Migrate clients
            if os.path.exists('data/clients.json'):
                import json
                with open('data/clients.json', 'r') as f:
                    clients = json.load(f)
                
                for client in clients:
                    # Convert datetime strings
                    if 'created_at' in client:
                        client['created_at'] = datetime.fromisoformat(client['created_at'].replace('Z', '+00:00'))
                    
                    try:
                        self.insert_client(client)
                        logger.info(f"Migrated client: {client['name']}")
                    except Exception as e:
                        logger.warning(f"Failed to migrate client {client['name']}: {e}")
            
            logger.info("Data migration completed")
        except Exception as e:
            logger.error(f"Migration failed: {e}")

# Global database instance
db = DatabaseManager()