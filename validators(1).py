import pandas as pd
import logging
from typing import List, Dict, Any, Optional
import re
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_csv_file(file: FileStorage) -> bool:
    """Validate uploaded CSV file format and content"""
    try:
        # Check file extension
        if not file.filename.lower().endswith('.csv'):
            raise ValidationError("File must be a CSV format")
        
        # Try to read the CSV
        try:
            df = pd.read_csv(file.stream)
            file.stream.seek(0)  # Reset stream position
        except Exception as e:
            raise ValidationError(f"Invalid CSV format: {str(e)}")
        
        # Check if file is empty
        if df.empty:
            raise ValidationError("CSV file is empty")
        
        # Check required columns
        required_columns = ['first_name', 'last_name', 'company', 'title', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Validate data quality
        validation_results = validate_lead_data(df)
        if validation_results['errors']:
            error_summary = f"Data validation failed: {len(validation_results['errors'])} errors found"
            logger.warning(error_summary)
            # Don't reject the file, but log warnings for data quality issues
        
        logger.info(f"CSV file validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating CSV: {e}")
        raise ValidationError(f"File validation failed: {str(e)}")

def validate_lead_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate lead data quality and return validation results"""
    errors = []
    warnings = []
    
    try:
        # Validate email addresses
        email_errors = validate_emails(df['email'].tolist())
        errors.extend(email_errors)
        
        # Check for empty required fields
        required_fields = ['first_name', 'last_name', 'company', 'title', 'email']
        for field in required_fields:
            if field in df.columns:
                empty_count = df[field].isna().sum() + (df[field] == '').sum()
                if empty_count > 0:
                    warnings.append(f"{empty_count} rows have empty {field}")
        
        # Validate names (basic checks)
        name_errors = validate_names(df)
        warnings.extend(name_errors)
        
        # Check for potential duplicates
        duplicate_emails = df['email'].duplicated().sum()
        if duplicate_emails > 0:
            warnings.append(f"{duplicate_emails} duplicate email addresses found")
        
        # Validate company names
        company_warnings = validate_companies(df['company'].tolist())
        warnings.extend(company_warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_rows': len(df),
            'duplicate_emails': duplicate_emails
        }
        
    except Exception as e:
        logger.error(f"Error validating lead data: {e}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': [],
            'total_rows': len(df) if 'df' in locals() else 0,
            'duplicate_emails': 0
        }

def validate_emails(emails: List[str]) -> List[str]:
    """Validate email addresses and return list of errors"""
    errors = []
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    for i, email in enumerate(emails):
        if pd.isna(email) or email == '':
            errors.append(f"Row {i+1}: Empty email address")
        elif not email_pattern.match(str(email)):
            errors.append(f"Row {i+1}: Invalid email format: {email}")
    
    return errors

def validate_names(df: pd.DataFrame) -> List[str]:
    """Validate name fields and return list of warnings"""
    warnings = []
    
    # Check first names
    if 'first_name' in df.columns:
        for i, name in enumerate(df['first_name']):
            if pd.isna(name) or str(name).strip() == '':
                continue
            if len(str(name).strip()) < 2:
                warnings.append(f"Row {i+1}: Suspiciously short first name: {name}")
            elif not re.match(r'^[a-zA-Z\s\-\'\.]+$', str(name)):
                warnings.append(f"Row {i+1}: Invalid characters in first name: {name}")
    
    # Check last names
    if 'last_name' in df.columns:
        for i, name in enumerate(df['last_name']):
            if pd.isna(name) or str(name).strip() == '':
                continue
            if len(str(name).strip()) < 2:
                warnings.append(f"Row {i+1}: Suspiciously short last name: {name}")
            elif not re.match(r'^[a-zA-Z\s\-\'\.]+$', str(name)):
                warnings.append(f"Row {i+1}: Invalid characters in last name: {name}")
    
    return warnings

def validate_companies(companies: List[str]) -> List[str]:
    """Validate company names and return list of warnings"""
    warnings = []
    
    for i, company in enumerate(companies):
        if pd.isna(company) or str(company).strip() == '':
            continue
        
        company_str = str(company).strip()
        
        # Check for suspiciously short company names
        if len(company_str) < 2:
            warnings.append(f"Row {i+1}: Suspiciously short company name: {company}")
        
        # Check for common placeholder text
        placeholder_patterns = ['test', 'example', 'sample', 'company', 'corp']
        if company_str.lower() in placeholder_patterns:
            warnings.append(f"Row {i+1}: Possible placeholder company name: {company}")
    
    return warnings

def validate_client_data(client_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate client data for new client creation"""
    errors = []
    
    # Required fields
    required_fields = ['name', 'plan', 'lead_count', 'email']
    for field in required_fields:
        if field not in client_data or not client_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate plan
    valid_plans = ['basic', 'pro', 'premium']
    if 'plan' in client_data and client_data['plan'] not in valid_plans:
        errors.append(f"Invalid plan. Must be one of: {', '.join(valid_plans)}")
    
    # Validate email
    if 'email' in client_data:
        email_errors = validate_emails([client_data['email']])
        if email_errors:
            errors.append(f"Invalid client email: {client_data['email']}")
    
    # Validate lead count
    if 'lead_count' in client_data:
        try:
            lead_count = int(client_data['lead_count'])
            if lead_count <= 0:
                errors.append("Lead count must be greater than 0")
            elif lead_count > 10000:
                errors.append("Lead count exceeds maximum limit (10,000)")
        except (ValueError, TypeError):
            errors.append("Lead count must be a valid number")
    
    # Validate monthly revenue
    if 'monthly_revenue' in client_data and client_data['monthly_revenue']:
        try:
            revenue = float(client_data['monthly_revenue'])
            if revenue < 0:
                errors.append("Monthly revenue cannot be negative")
        except (ValueError, TypeError):
            errors.append("Monthly revenue must be a valid number")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s\-_\.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')

def validate_file_size(file: FileStorage, max_size_mb: int = 10) -> bool:
    """Validate file size"""
    try:
        # Get file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if size > max_size_bytes:
            raise ValidationError(f"File size ({size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
        
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validating file size: {e}")
        raise ValidationError("Could not validate file size")

def validate_csv_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate CSV structure and data types"""
    issues = []
    
    # Check column names for common issues
    for col in df.columns:
        if col != col.strip():
            issues.append(f"Column '{col}' has leading/trailing whitespace")
        if ' ' in col and '_' not in col:
            issues.append(f"Column '{col}' uses spaces instead of underscores")
    
    # Check for completely empty rows
    empty_rows = df.isnull().all(axis=1).sum()
    if empty_rows > 0:
        issues.append(f"{empty_rows} completely empty rows found")
    
    # Check data type consistency
    for col in df.columns:
        if col in ['first_name', 'last_name', 'company', 'title']:
            non_string_count = df[col].apply(lambda x: not isinstance(x, str) and pd.notna(x)).sum()
            if non_string_count > 0:
                issues.append(f"Column '{col}' contains {non_string_count} non-string values")
    
    return {
        'issues': issues,
        'row_count': len(df),
        'column_count': len(df.columns),
        'empty_rows': empty_rows
    }
