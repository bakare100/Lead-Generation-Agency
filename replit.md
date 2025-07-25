# AILeadGen - Automated Lead Generation System

## Overview

AILeadGen is a comprehensive lead generation and delivery platform that automates the process of processing, personalizing, and delivering leads to clients. The system features AI-powered personalization, automated scheduling, client management, and multi-service integrations including Notion CRM, Google Drive, and email delivery.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: Service-oriented architecture with modular components
- **Data Models**: Dataclass-based models for Lead and Client entities
- **Configuration Management**: Environment-based configuration with fallback defaults
- **Logging**: Structured logging with file and console handlers

### Frontend Architecture
- **Technology**: Server-side rendered HTML templates with Bootstrap 5
- **JavaScript**: Vanilla JavaScript for interactive components
- **Styling**: Custom CSS with Bootstrap integration
- **UI Pattern**: Responsive design with dashboard-style interface

### Data Storage
- **Primary Storage**: PostgreSQL database for all client, lead, and delivery data
- **Database Schema**: Comprehensive tables with proper indexing and relationships
- **Migration Support**: Automatic migration from JSON files to database
- **Temporary Storage**: Local file system for uploaded CSV files
- **External Storage**: Google Drive integration for file sharing
- **CRM Integration**: Notion database for delivery tracking

## Key Components

### Core Services

1. **Lead Processor** (`services/lead_processor.py`)
   - Main orchestration service for lead processing workflow
   - Coordinates AI personalization, deduplication, and delivery
   - Handles CSV file processing and data validation

2. **AI Personalizer** (`services/ai_personalizer.py`)
   - Google Gemini AI integration for personalized email generation
   - Generates custom cold emails and icebreakers
   - Fallback functionality when AI service unavailable

3. **Scheduler Service** (`services/scheduler.py`)
   - Automated task scheduling using Python schedule library
   - Background thread execution for non-blocking operations
   - Daily processing automation

4. **Email Service** (`services/email_service.py`)
   - SMTP-based email delivery system
   - Delivery notifications and commission reminders
   - HTML and text email template support

5. **Google Drive Service** (`services/google_drive.py`)
   - File upload and sharing functionality
   - Service account authentication
   - Automated folder organization

6. **Notion CRM** (`services/notion_crm.py`)
   - Integration with Notion databases
   - Delivery logging and tracking
   - Client relationship management

### Utility Services

1. **Deduplication Service** (`utils/deduplication.py`)
   - Email-based duplicate detection
   - Time-window based filtering
   - Cross-delivery duplicate prevention

2. **Validators** (`utils/validators.py`)
   - CSV file format validation
   - Data quality checks
   - Email format validation

### Data Models

- **Lead Model**: Comprehensive lead data structure with personalization fields
- **Client Model**: Client account information with plan configurations
- **Configuration Model**: Environment-based settings management

## Data Flow

1. **Lead Upload**: CSV files uploaded through web interface
2. **Validation**: File format and data quality validation
3. **Deduplication**: Remove internal and historical duplicates
4. **AI Processing**: Generate personalized emails and icebreakers
5. **Client Allocation**: Distribute leads based on client plans and quotas
6. **File Generation**: Create deliverable CSV files per client
7. **Cloud Upload**: Upload files to Google Drive with sharing permissions
8. **Email Delivery**: Send notification emails with download links
9. **CRM Logging**: Record delivery details in Notion database

## External Dependencies

### Required API Keys
- **GEMINI_API_KEY**: Google Gemini AI for personalization (✓ Configured)
- **GOOGLE_DRIVE_CREDENTIALS**: Service account JSON for file operations
- **NOTION_INTEGRATION_SECRET**: Notion API access token (✓ Configured)
- **NOTION_DATABASE_ID**: Notion database ID for CRM tracking (✓ Configured)
- **EMAIL_USER/PASSWORD**: SMTP credentials for email delivery

### Third-Party Services
- **Google Gemini AI**: Text generation and personalization
- **Google Drive API**: File storage and sharing
- **Notion API**: CRM and delivery tracking
- **SMTP Service**: Email delivery (configurable provider)

### Python Dependencies
- **Flask**: Web framework and routing
- **Pandas**: CSV processing and data manipulation
- **Google Client Libraries**: Drive and AI service integration
- **Requests**: HTTP client for API interactions
- **Schedule**: Task scheduling and automation

## Deployment Strategy

### Environment Configuration
- Environment variables for all sensitive credentials
- Configurable SMTP settings for different email providers
- Flexible storage paths for uploads and data files
- Development/production configuration separation

### File System Requirements
- Write permissions for uploads and data directories
- Local storage for temporary CSV processing
- Persistent storage for client and lead databases

### Service Dependencies
- External API connectivity for Google and Notion services
- SMTP server access for email delivery
- Sufficient storage space for file processing

### Scalability Considerations
- File-based storage suitable for moderate lead volumes
- Service-oriented architecture allows for easy component replacement
- Background processing prevents UI blocking during heavy operations
- Configurable batch sizes for lead processing optimization

The system is designed for small to medium-scale lead generation operations with the flexibility to integrate additional services or migrate to database storage as needed.