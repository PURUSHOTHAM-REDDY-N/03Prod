#!/usr/bin/env python
"""
Simple script to check if confidence tables exist and have data.
"""

import os
import sys
from run import app
from app import db

def check_tables():
    """Check if confidence tables exist and have data."""
    with app.app_context():
        try:
            # Check database tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("Available database tables:")
            for table in tables:
                print(f"- {table}")
            
            print("\nChecking for confidence tables...")
            if 'subtopic_confidences' in tables:
                print("✓ subtopic_confidences table exists")
                
                # Count records
                result = db.session.execute(db.text("SELECT COUNT(*) FROM subtopic_confidences")).scalar()
                print(f"  Contains {result} records")
                
                # Sample data
                if result > 0:
                    sample = db.session.execute(db.text("SELECT * FROM subtopic_confidences LIMIT 3")).fetchall()
                    print("  Sample data:")
                    for row in sample:
                        print(f"  - {row}")
            else:
                print("✗ subtopic_confidences table NOT found")
            
            if 'topic_confidences' in tables:
                print("✓ topic_confidences table exists")
                
                # Count records
                result = db.session.execute(db.text("SELECT COUNT(*) FROM topic_confidences")).scalar()
                print(f"  Contains {result} records")
                
                # Sample data
                if result > 0:
                    sample = db.session.execute(db.text("SELECT * FROM topic_confidences LIMIT 3")).fetchall()
                    print("  Sample data:")
                    for row in sample:
                        print(f"  - {row}")
            else:
                print("✗ topic_confidences table NOT found")
                
            print("\nTEST COMPLETE")
            
        except Exception as e:
            print(f"Error checking tables: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_tables()
