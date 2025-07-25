from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

@dataclass
class Lead:
    """Lead data model"""
    lead_id: str
    client_name: str
    first_name: str
    last_name: str
    title: str
    company: str
    email: str
    linkedin: str
    cold_email: str
    icebreaker: str
    verified: bool
    exclusive: bool
    created_at: datetime
    delivered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary"""
        return {
            'Lead ID': self.lead_id,
            'Client Name': self.client_name,
            'First Name': self.first_name,
            'Last Name': self.last_name,
            'Title': self.title,
            'Company': self.company,
            'Email': self.email,
            'LinkedIn': self.linkedin,
            'Cold Email': self.cold_email,
            'Icebreaker': self.icebreaker,
            'Verified': '✅' if self.verified else '❌',
            'Exclusive': 'Yes' if self.exclusive else 'No',
            'Created At': self.created_at.isoformat(),
            'Delivered At': self.delivered_at.isoformat() if self.delivered_at else ''
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create lead from dictionary"""
        return cls(
            lead_id=data['Lead ID'],
            client_name=data['Client Name'],
            first_name=data['First Name'],
            last_name=data['Last Name'],
            title=data['Title'],
            company=data['Company'],
            email=data['Email'],
            linkedin=data['LinkedIn'],
            cold_email=data['Cold Email'],
            icebreaker=data['Icebreaker'],
            verified=data['Verified'] == '✅',
            exclusive=data['Exclusive'] == 'Yes',
            created_at=datetime.fromisoformat(data['Created At']),
            delivered_at=datetime.fromisoformat(data['Delivered At']) if data['Delivered At'] else None
        )

@dataclass
class Client:
    """Client data model"""
    id: int
    name: str
    plan: str
    exclusive: bool
    lead_count: int
    email: str
    monthly_revenue: float
    remaining_quota: int
    created_at: datetime
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'plan': self.plan,
            'exclusive': self.exclusive,
            'lead_count': self.lead_count,
            'email': self.email,
            'monthly_revenue': self.monthly_revenue,
            'remaining_quota': self.remaining_quota,
            'created_at': self.created_at.isoformat(),
            'active': self.active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """Create client from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            plan=data['plan'],
            exclusive=data['exclusive'],
            lead_count=data['lead_count'],
            email=data['email'],
            monthly_revenue=data['monthly_revenue'],
            remaining_quota=data['remaining_quota'],
            created_at=datetime.fromisoformat(data['created_at']),
            active=data.get('active', True)
        )

@dataclass
class Delivery:
    """Delivery tracking model"""
    id: str
    client_id: int
    client_name: str
    leads_count: int
    file_path: str
    google_drive_url: str
    status: str
    created_at: datetime
    delivered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert delivery to dictionary"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client_name,
            'leads_count': self.leads_count,
            'file_path': self.file_path,
            'google_drive_url': self.google_drive_url,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else ''
        }

@dataclass
class CommissionRecord:
    """Commission tracking model"""
    id: str
    client_id: int
    client_name: str
    amount: float
    commission_rate: float
    commission_amount: float
    period: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert commission record to dictionary"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client_name,
            'amount': self.amount,
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'period': self.period,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else ''
        }
