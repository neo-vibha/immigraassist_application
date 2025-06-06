from flask import Flask
from models import db
import pymysql

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Venus%402002@localhost/immigraassist'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Add new columns to the petitions table
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Venus@2002',
            database='immigraassist'
        )
        
        with connection.cursor() as cursor:
            # Check if columns already exist
            cursor.execute("SHOW COLUMNS FROM petitions LIKE 'form_data'")
            form_data_exists = cursor.fetchone()
            
            cursor.execute("SHOW COLUMNS FROM petitions LIKE 'feedback'")
            feedback_exists = cursor.fetchone()
            
            cursor.execute("SHOW COLUMNS FROM petitions LIKE 'admin_notes'")
            admin_notes_exists = cursor.fetchone()
            
            # Add columns if they don't exist
            if not form_data_exists:
                cursor.execute("ALTER TABLE petitions ADD COLUMN form_data TEXT")
                print("Added form_data column")
            
            if not feedback_exists:
                cursor.execute("ALTER TABLE petitions ADD COLUMN feedback TEXT")
                print("Added feedback column")
            
            if not admin_notes_exists:
                cursor.execute("ALTER TABLE petitions ADD COLUMN admin_notes TEXT")
                print("Added admin_notes column")
            
            connection.commit()
            print("Database schema updated successfully")
            
    except Exception as e:
        print(f"Error updating database schema: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
