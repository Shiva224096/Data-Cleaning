"""
DataScrub Backend Configuration
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Upload directory
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Maximum rows to profile in preview
PROFILE_PREVIEW_ROWS = 100

# Default fuzzy matching threshold for company names
DEFAULT_FUZZY_THRESHOLD = 85

# Default phone region
DEFAULT_PHONE_REGION = "US"

# Column type categories
COLUMN_TYPES = [
    "email",
    "phone",
    "name",
    "company",
    "date",
    "number",
    "url",
    "ip_address",
    "financial",
    "pan",
    "gst",
    "ssn",
    "uuid",
    "isbn",
    "vin",
    "mac_address",
    "hex_color",
    "zip_code",
    "text",
]

# WebSocket message types
WS_PROGRESS = "progress"
WS_COLUMN_DONE = "column_done"
WS_COMPLETE = "complete"
WS_ERROR = "error"

# Issue status separator
ISSUE_SEPARATOR = "; "
