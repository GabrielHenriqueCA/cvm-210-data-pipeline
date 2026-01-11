"""
AWS Lambda Function for CVM 210 Daily Data Ingestion.

This function automatically downloads CVM fund data from the public website,
extracts CSV files from ZIP archives, and uploads them to S3 in a partitioned
structure (ano=YYYY/mes=MM/).

Environment Variables:
    S3_BUCKET: Target S3 bucket name
    S3_PREFIX: S3 key prefix (default: cvm-transactions-daily)
    CVM_BASE_URL: Base URL for CVM data (default: https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/)
"""

import boto3
import urllib3
import io
import zipfile
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants with defaults (can be overridden by environment variables)
# ⚠️ IMPORTANT: Configure these environment variables in the AWS Lambda Console
S3_BUCKET = os.environ.get('S3_BUCKET')
if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable is required!")
    
S3_PREFIX = os.environ.get('S3_PREFIX', 'cvm-transactions-daily')
CVM_BASE_URL = os.environ.get('CVM_BASE_URL', 'https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/')
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.
    
    Downloads CVM 210 fund data from the public website, extracts CSV files
    from ZIP archives, and uploads to S3 with year/month partitioning.
    
    Args:
        event: Lambda event object (not currently used)
        context: Lambda context object
        
    Returns:
        Dictionary with statusCode and body describing the operation result
        
    Example Response:
        {
            'statusCode': 200,
            'body': 'Successfully processed inf_diario_fi_202401.zip to s3://bucket/path/file.csv'
        }
    """
    logger.info("Starting CVM 210 daily data ingestion")
    
    try:
        # Initialize AWS and HTTP clients
        s3_client = boto3.client('s3')
        http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=10.0, read=60.0),
            retries=urllib3.Retry(total=MAX_RETRIES, backoff_factor=RETRY_DELAY_SECONDS)
        )
        
        # Get dates to try (current month and previous month)
        dates_to_try = _get_dates_to_try()
        
        # Try each date until successful
        for attempt_date in dates_to_try:
            year, month = attempt_date.strftime("%Y"), attempt_date.strftime("%m")
            file_name = f"inf_diario_fi_{year}{month}.zip"
            url = f"{CVM_BASE_URL}{file_name}"
            
            logger.info(f"Attempting to download: {file_name} from {url}")
            
            try:
                # Download and process the file
                success, message, s3_key = _download_and_process_file(
                    http, s3_client, url, year, month, file_name
                )
                
                if success:
                    logger.info(f"Successfully processed {file_name}")
                    return {
                        'statusCode': 200,
                        'body': f'Successfully processed {file_name} to s3://{S3_BUCKET}/{s3_key}'
                    }
                else:
                    logger.warning(f"Failed to process {file_name}: {message}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_name}: {str(e)}", exc_info=True)
                continue
        
        # If we get here, all attempts failed
        error_msg = "No CVM data file found for current or previous month"
        logger.error(error_msg)
        return {
            'statusCode': 404,
            'body': error_msg
        }
        
    except Exception as e:
        error_msg = f"Unexpected error in Lambda handler: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': error_msg
        }


def _get_dates_to_try() -> List[datetime]:
    """
    Get list of dates to try for downloading CVM data.
    
    Returns current month and previous month dates.
    
    Returns:
        List of datetime objects to attempt
    """
    now = datetime.now()
    current_month = now
    previous_month = now.replace(day=1) - timedelta(days=1)
    
    return [current_month, previous_month]


def _download_and_process_file(
    http: urllib3.PoolManager,
    s3_client: boto3.client,
    url: str,
    year: str,
    month: str,
    file_name: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Download a ZIP file from CVM, extract CSV, and upload to S3.
    
    Args:
        http: urllib3 PoolManager instance
        s3_client: boto3 S3 client
        url: URL to download from
        year: Year string (YYYY format)
        month: Month string (MM format)
        file_name: Name of the file being processed
        
    Returns:
        Tuple of (success: bool, message: str, s3_key: Optional[str])
    """
    try:
        # Download the file
        logger.info(f"Downloading from {url}")
        response = http.request('GET', url, preload_content=False)
        
        if response.status != 200:
            return False, f"HTTP {response.status}", None
        
        # Read ZIP content into memory
        logger.info("Reading ZIP content")
        zip_buffer = io.BytesIO(response.read())
        response.release_conn()
        
        # Extract and upload CSV
        with zipfile.ZipFile(zip_buffer) as zip_file:
            # Find CSV file in ZIP
            csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
            
            if not csv_files:
                return False, "No CSV file found in ZIP archive", None
            
            if len(csv_files) > 1:
                logger.warning(f"Multiple CSV files found, using first: {csv_files[0]}")
            
            csv_name = csv_files[0]
            logger.info(f"Extracting {csv_name} from ZIP")
            
            # Read CSV content
            with zip_file.open(csv_name) as csv_file:
                csv_content = csv_file.read()
                
                # Construct S3 key with partitioning
                s3_key = f"{S3_PREFIX}/ano={year}/mes={month}/{csv_name}"
                
                # Upload to S3
                logger.info(f"Uploading to s3://{S3_BUCKET}/{s3_key}")
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=csv_content,
                    Metadata={
                        'source': 'CVM',
                        'file_type': 'inf_diario_fi',
                        'processing_date': datetime.now().isoformat(),
                        'original_file': file_name
                    }
                )
                
                logger.info(f"Successfully uploaded {len(csv_content)} bytes to S3")
                return True, "Success", s3_key
                
    except zipfile.BadZipFile as e:
        return False, f"Invalid ZIP file: {str(e)}", None
    except ClientError as e:
        return False, f"S3 error: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None
