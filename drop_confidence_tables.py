#!/usr/bin/env python
"""
Script to drop confidence-related tables from the database.
"""

from flask import Flask
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

# Create minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def drop_confidence_tables():
    """Drop all confidence-related tables from the database."""
    with app.app_context():
        # Create a database connection
        connection = db.engine.connect()
        
        # Execute raw SQL to drop the tables
        try:
            # Drop subtopic_confidences table
            connection.execute(text("DROP TABLE IF EXISTS subtopic_confidences"))
            
            # Drop topic_confidences table
            connection.execute(text("DROP TABLE IF EXISTS topic_confidences"))
            
            # Commit the transaction
            connection.commit()
            
            print("Confidence tables successfully dropped.")
        except Exception as e:
            print(f"Error dropping confidence tables: {e}")
        finally:
            # Close the connection
            connection.close()

if __name__ == "__main__":
    drop_confidence_tables()
