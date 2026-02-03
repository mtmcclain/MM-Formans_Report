"""
Configuration settings for MM-Formans_Report application
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Data directory
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database path
DB_PATH = DATA_DIR / "reports.db"

# Users file path (for initial authentication)
USERS_FILE = DATA_DIR / "users.yaml"

# PDF templates
PDF_TEMPLATE_DIR = BASE_DIR
BLANK_FOREMAN_REPORT = PDF_TEMPLATE_DIR / "BlankForemanReport.pdf"

# Application settings
MAX_EMPLOYEES_PER_REPORT = 13
WEEK_START_DAY = 0  # Monday (0 = Monday, 6 = Sunday)
