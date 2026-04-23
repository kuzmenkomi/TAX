#!/usr/bin/env python
"""Script to create database tables"""
import sys
sys.path.insert(0, r'C:\Users\kuzme\Tax\backend')

from app.core.db import Base, engine
import app.models  # Import all models to register them with SQLAlchemy

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# Verify tables were created
import sqlite3
conn = sqlite3.connect(r'C:\Users\kuzme\Tax\backend\tax_app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nTables in database: {[t[0] for t in tables]}")
conn.close()
