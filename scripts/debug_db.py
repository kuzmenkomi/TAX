#!/usr/bin/env python
"""Debug database configuration"""
import sys
import os
sys.path.insert(0, r'C:\Users\kuzme\Tax\backend')

# Load .env first
from dotenv import load_dotenv
load_dotenv(r'C:\Users\kuzme\Tax\backend\.env')

from app.core.db import DATABASE_URL, engine, Base

print(f"DATABASE_URL: {DATABASE_URL}")
print(f"Engine URL: {engine.url}")
print(f"Engine dialect: {engine.dialect.name}")

# Check if file exists
import re
sqlite_match = re.match(r'sqlite:///\.?(.*)', DATABASE_URL)
if sqlite_match:
    db_file = sqlite_match.group(1)
    if not db_file.startswith('/'):
        db_file = os.path.join(r'C:\Users\kuzme\Tax\backend', db_file)
    print(f"Database file: {db_file}")
    print(f"File exists: {os.path.exists(db_file)}")
