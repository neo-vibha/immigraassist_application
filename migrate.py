from flask import Flask
from sqlalchemy import text
from models import db
import os
from urllib.parse import quote

# Create a minimal Flask app for migration
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Venus%402002@localhost/immigraassist'
password = quote("123Qwerty!@#")
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{password}@127.0.0.1/immigraassist"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def run_migration():
    """Add new required fields to the Petition table."""
    print("Starting database migration...")
    
    try:
        with app.app_context():
            # Check if columns exist before adding them
            with db.engine.connect() as conn:
                # Check if passport_number column exists
                result = conn.execute(text("SHOW COLUMNS FROM petitions LIKE 'passport_number'"))
                if not result.fetchone():
                    print("Adding passport_number column...")
                    conn.execute(text("ALTER TABLE petitions ADD COLUMN passport_number VARCHAR(50) DEFAULT 'MIGRATION-ADD-NUMBER' NOT NULL"))
                    
                # Check if passport_expiry_date column exists
                result = conn.execute(text("SHOW COLUMNS FROM petitions LIKE 'passport_expiry_date'"))
                if not result.fetchone():
                    print("Adding passport_expiry_date column...")
                    conn.execute(text("ALTER TABLE petitions ADD COLUMN passport_expiry_date DATE DEFAULT '2030-01-01' NOT NULL"))
                
                # Check if education_qualification column exists
                result = conn.execute(text("SHOW COLUMNS FROM petitions LIKE 'education_qualification'"))
                if not result.fetchone():
                    print("Adding education_qualification column...")
                    conn.execute(text("ALTER TABLE petitions ADD COLUMN education_qualification VARCHAR(255) DEFAULT 'Please update' NOT NULL"))
                
                print("Migration completed successfully!")
                
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        print("Migration failed.")
        
if __name__ == "__main__":
    run_migration()
