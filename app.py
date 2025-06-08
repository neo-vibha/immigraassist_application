from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from models import User, Petition, db
import os
import re
from markupsafe import Markup
from urllib.parse import quote
from flask import Flask, request, jsonify,  render_template, session,flash, redirect, url_for
from werkzeug.utils import secure_filename
from ocr_processing import ( extract_text_from_file, extract_cv_features,  extract_passport_data,
                            extract_text_from_certificate, extract, extract_text_from_word, preprocess, compare)
from backend.verify_docs import compare_passport_pdf_to_reference
import traceback
from transformers import T5ForConditionalGeneration, T5Tokenizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from backend.helper_functions import allowed_file, rename_keys_in_place
import mysql.connector
from datetime import datetime
import re


# Inside your Flask route or function
passport_ref_file_path = os.path.join(os.getcwd(), 'static', 'supporting_doc', 'indian.jpg')
employer_ref_file_path = os.path.join(os.getcwd(), 'static', 'supporting_doc', 'Employee Support Letter_ref.docx')

app = Flask(__name__)
app.secret_key = 'your-very-secure-secret-key'  # use a long, random key in production

model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")
model_emp = SentenceTransformer('paraphrase-MiniLM-L6-v2')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
password = quote("123Qwerty!@#")

# Define the nl2br filter
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        value = str(value)
        return Markup(value.replace('\n', '<br>\n'))
    return ''

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Venus%402002@localhost/immigraassist'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{password}@127.0.0.1/immigraassist"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False  # Temporarily disable CSRF for testing


# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('is_admin'):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def attorney_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not (session.get('is_admin') or session.get('is_attorney')):
            flash('Access denied. Attorney privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_document_icon(doc_type):
    # Return appropriate FontAwesome icon class based on document type
    icon_map = {
        'Passport': 'fa-passport',
        'Birth Certificate': 'fa-file-alt',
        'Marriage Certificate': 'fa-file-contract',
        'Employment Letter': 'fa-file-signature',
        'Academic Transcript': 'fa-file-alt',
        'Tax Return': 'fa-file-invoice-dollar',
        'I-94 Record': 'fa-file-alt',
        'Previous Visa': 'fa-id-card'
    }
    
    # Return the mapped icon or a default icon if not found
    return icon_map.get(doc_type, 'fa-file')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query user by email
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password) and user.role == 'admin':
            session['logged_in'] = True
            session['user_id'] = user.id
            session['is_admin'] = True
            session['admin_name'] = f"{user.firstname} {user.lastname}"
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid email or password or insufficient permissions.', 'error')

    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query user by email
        user = User.query.filter_by(email=email).first()

        print(user.firstname)

        if user and check_password_hash(user.password, password):
            # Check for orphaned petitions associated with this email but not with this user
            # This ensures data persistence across login sessions with the same email
            orphaned_petitions = Petition.query.filter(
                Petition.email == email,
                Petition.user_id != user.id
            ).all()
            
            # If there are orphaned petitions, associate them with the current user
            if orphaned_petitions:
                print(f"Found {len(orphaned_petitions)} orphaned petitions for email {email}. Associating with user {user.id}")
                for petition in orphaned_petitions:
                    petition.user_id = user.id
                db.session.commit()
            
            session.clear()
            session['logged_in'] = True
            session['user_id'] = user.id
            session['email'] = email  # Store the user's email in the session for petition lookups
            session['is_admin'] = user.role == 'admin' or user.role == 'Admin'  # Admin has admin access
            session['is_attorney'] = user.role == 'attorney' or user.role == 'Attorney'  # Attorney role
            session['admin_name'] = f"{user.firstname} {user.lastname}" if user.role == 'admin' or user.role == 'Admin' else ''
            session['attorney_name'] = f"{user.firstname} {user.lastname}" if user.role == 'attorney' or user.role == 'Attorney' else ''
            flash('Logged in successfully!', 'success')
            if user.role == 'Admin' or user.role == 'admin':
                return redirect(url_for('attorney'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form.get('firstName')
        lastname = request.form.get('lastName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            phone=phone,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Get the current user's ID from session
    user_id = session.get('user_id')
    
    # Check if the user has any existing petitions
    existing_petition = None
    if user_id:
        existing_petition = Petition.query.filter_by(user_id=user_id).order_by(Petition.created_at.desc()).first()
    
    if request.method == 'POST':
        try:
            # Debug: Print form data
            print("\n" + "="*50)
            print("FORM SUBMISSION RECEIVED")
            print("="*50)
            print("Form submitted with data:")
            for key, value in request.form.items():
                print(f"{key}: {value}")
            print("="*50 + "\n")
            
            # Get the current user's ID from session
            user_id = session.get('user_id')
            
            # TEMPORARY SOLUTION FOR TESTING: Use Admin user if no user is in session
            if not user_id:
                # Find Admin user or create one if it doesn't exist
                Admin_user = User.query.filter_by(email='Admin@example.com').first()
                if not Admin_user:
                    print("Creating Admin user for testing")
                    Admin_user = User(
                        firstname='Admin',
                        lastname='User',
                        email='Admin@example.com',
                        phone='1234567890',
                        password=generate_password_hash('Admin123'),
                        role='Admin'
                    )
                    db.session.add(Admin_user)
                    db.session.commit()
                
                user_id = Admin_user.id
                print(f"Using Admin user (id: {user_id}) for testing")
            else:
                # Verify the user exists in the database
                user = User.query.get(user_id)
                if not user:
                    # Find or create Admin user as fallback
                    Admin_user = User.query.filter_by(email='Admin@example.com').first()
                    if not Admin_user:
                        Admin_user = User(
                            firstname='Admin',
                            lastname='User',
                            email='Admin@example.com',
                            phone='1234567890',
                            password=generate_password_hash('Admin123'),
                            role='Admin'
                        )
                        db.session.add(Admin_user)
                        db.session.commit()
                    
                    user_id = Admin_user.id
                    print(f"User not found, using Admin user (id: {user_id}) for testing")
                else:
                    print(f"Processing form for user_id: {user_id}, user: {user.email}")
            
            # Process birth date
            birth_date = None
            if request.form.get('birthDate'):
                try:
                    birth_date = datetime.strptime(request.form['birthDate'], '%Y-%m-%d')
                    print(f"Parsed birth date: {birth_date}")
                except ValueError as e:
                    print(f"Error parsing birth date: {e}")
                    flash('Invalid date format for birth date', 'error')
                    return redirect(url_for('dashboard'))
            
            # Create a new petition with form data
            petition = Petition(
                user_id=user_id,
                
                # Part 1: Petitioner Information
                petitioner_family_name=request.form['petitionerFamilyName'],
                petitioner_given_name=request.form['petitionerGivenName'],
                petitioner_middle_name=request.form.get('petitionerMiddleName', ''),
                company_name=request.form['companyName'],
                in_care_of=request.form.get('inCareOf', ''),
                street_address=request.form.get('streetAddress', ''),
                apt_ste_flr=request.form.get('aptSteFlr', ''),
                city=request.form.get('city', ''),
                state=request.form.get('state', ''),
                zip_code=request.form.get('zipCode', ''),
                province=request.form.get('province', ''),
                postal_code=request.form.get('postalCode', ''),
                country=request.form.get('country', ''),
                daytime_phone=request.form['daytimePhone'],
                mobile_phone=request.form.get('mobilePhone', ''),
                email=request.form['email'],
                fein=request.form['fein'],
                
                # Part 2: Basis for Classification
                basis_for_classification=request.form['basisForClassification'],
                
                # Part 3: Beneficiary Information
                beneficiary_family_name=request.form['beneficiaryFamilyName'],
                beneficiary_given_name=request.form['beneficiaryGivenName'],
                beneficiary_middle_name=request.form.get('beneficiaryMiddleName', ''),
                other_family_name=request.form.get('otherFamilyName', ''),
                other_given_name=request.form.get('otherGivenName', ''),
                other_middle_name=request.form.get('otherMiddleName', ''),
                birth_date=birth_date,
                gender=request.form.get('gender', ''),
                ssn=request.form.get('ssn', ''),
                alien_number=request.form.get('alienNumber', ''),
                country_of_birth=request.form['countryOfBirth'],
                country_of_citizenship=request.form['countryOfCitizenship'],
                passport_number=request.form['passportNumber'],
                passport_expiry_date=datetime.strptime(request.form['passportExpiryDate'], '%Y-%m-%d'),
                education_qualification=request.form['educationQualification'],
                
                # Part 4: Processing Information
                foreign_street=request.form.get('foreignStreet', ''),
                foreign_apt=request.form.get('foreignApt', ''),
                foreign_city=request.form.get('foreignCity', ''),
                foreign_state=request.form.get('foreignState', ''),
                foreign_postal=request.form.get('foreignPostal', ''),
                foreign_country=request.form.get('foreignCountry', ''),
                valid_passport=request.form.get('validPassport', ''),
                passport_explanation=request.form.get('passportExplanation', ''),
                
                # Part 5: Basic Information About Proposed Employment
                job_title=request.form['jobTitle'],
                lca_number=request.form['lcaNumber'],
                work_street_1=request.form.get('workStreet1', ''),
                work_apt_1=request.form.get('workApt1', ''),
                work_city_1=request.form.get('workCity1', ''),
                work_state_1=request.form.get('workState1', ''),
                work_zip_1=request.form.get('workZip1', ''),
                third_party_1=request.form.get('thirdParty1', 'no'),
                third_party_org_1=request.form.get('thirdPartyOrg1', ''),
                itinerary=request.form.get('itinerary', 'no'),
                work_offsite=request.form.get('workOffsite', 'no'),
                full_time=request.form.get('fullTime', 'yes'),
                hours_per_week=int(request.form.get('hoursPerWeek', 0)) if request.form.get('hoursPerWeek') else None,
                wage_amount=float(request.form.get('wageAmount', 0)) if request.form.get('wageAmount') else 0,
                wage_period=request.form.get('wagePeriod', '')
            )
            
            print("Petition object created successfully")
            
            # Add to database and commit
            db.session.add(petition)
            print("Petition added to session")
            db.session.commit()
            print("Database commit successful")
            
            # Show success message
            flash('Petition submitted successfully!', 'success')
            
            # Return a response that will trigger the document requirements page
            return render_template('dashboard.html', 
                                  show_documents=True, 
                                  petition_submitted=True)

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting petition: {str(e)}', 'error')
            print(f"Exception details: {str(e)}")
            # Print the full traceback for debugging
            import traceback
            traceback.print_exc()

    return render_template('dashboard.html', existing_petition=existing_petition)
    
@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash('Message sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/attorney/i129-form/<int:petition_id>', methods=['GET'])
@attorney_required
def attorney_i129_form(petition_id):
    # Get petition details from database
    petition = Petition.query.join(User).filter(Petition.id == petition_id).first()
    
    if not petition:
        flash('Petition not found', 'error')
        return redirect(url_for('admin'))
    
    # Map the petition state to a user-friendly string
    state_display = {
        'approved': 'Approved',
        'under_review': 'Under Review',
        'pending': 'Pending',
        'needs_info': 'Needs Information'
    }
    
    state = state_display.get(petition.state.lower() if petition.state else 'pending', 'Pending')
    
    return render_template('attorney_i129_form.html', petition=petition, state=state)

@app.route('/attorney/i140-form/<int:petition_id>', methods=['GET'])
@attorney_required
def attorney_i140_form(petition_id):
    # Get petition details from database
    petition = Petition.query.join(User).filter(Petition.id == petition_id).first()
    
    if not petition:
        flash('Petition not found', 'error')
        return redirect(url_for('admin'))
    
    # Map the petition state to a user-friendly string
    state_display = {
        'approved': 'Approved',
        'under_review': 'Under Review',
        'pending': 'Pending',
        'needs_info': 'Needs Information'
    }
    
    state = state_display.get(petition.state.lower() if petition.state else 'pending', 'Pending')
    
    return render_template('attorney_i140_form.html', petition=petition, state=state)

@app.route('/attorney/update-i129/<int:petition_id>', methods=['POST'])
@attorney_required
def update_i129_petition(petition_id):
    petition = Petition.query.get(petition_id)
    
    if not petition:
        flash('Petition not found', 'error')
        return redirect(url_for('admin'))
    
    # Update petition fields from form data
    # Company/Petitioner Information
    petition.company_name = request.form.get('company_name', petition.company_name)
    petition.trade_name = request.form.get('trade_name')
    petition.street_address = request.form.get('street_address', petition.street_address)
    petition.apt_ste_flr = request.form.get('apt_ste_flr')
    petition.city = request.form.get('city', petition.city)
    petition.state = request.form.get('state', petition.state) # State field conflicts with petition status field
    petition.zip_code = request.form.get('zip_code', petition.zip_code)
    petition.country = request.form.get('country', petition.country)
    petition.fein = request.form.get('fein', petition.fein)
    petition.email = request.form.get('email', petition.email)
    petition.daytime_phone = request.form.get('daytime_phone', petition.daytime_phone)
    petition.mobile_phone = request.form.get('mobile_phone')
    
    # Petition Information
    petition.basis_for_classification = request.form.get('classification', petition.basis_for_classification)
    petition.petition_type = request.form.get('petition_type', petition.petition_type)
    petition.lca_number = request.form.get('lca_number', petition.lca_number)
    petition.requested_start_date = request.form.get('requested_start_date', petition.requested_start_date)
    petition.requested_end_date = request.form.get('requested_end_date', petition.requested_end_date)
    
    # Beneficiary Information
    petition.beneficiary_family_name = request.form.get('beneficiary_family_name', petition.beneficiary_family_name)
    petition.beneficiary_given_name = request.form.get('beneficiary_given_name', petition.beneficiary_given_name)
    petition.beneficiary_middle_name = request.form.get('beneficiary_middle_name')
    petition.other_family_name = request.form.get('other_family_name')
    petition.other_given_name = request.form.get('other_given_name')
    petition.other_middle_name = request.form.get('other_middle_name')
    petition.birth_date = request.form.get('birth_date', petition.birth_date)
    petition.gender = request.form.get('gender', petition.gender)
    petition.country_of_birth = request.form.get('country_of_birth', petition.country_of_birth)
    petition.country_of_citizenship = request.form.get('country_of_citizenship', petition.country_of_citizenship)
    petition.alien_number = request.form.get('alien_number')
    petition.ssn = request.form.get('ssn')
    petition.passport_number = request.form.get('passport_number', petition.passport_number)
    petition.passport_expiry_date = request.form.get('passport_expiry_date', petition.passport_expiry_date)
    petition.foreign_street = request.form.get('foreign_street', petition.foreign_street)
    petition.foreign_apt = request.form.get('foreign_apt')
    petition.foreign_city = request.form.get('foreign_city', petition.foreign_city)
    petition.foreign_state = request.form.get('foreign_state')
    petition.foreign_postal = request.form.get('foreign_postal')
    petition.foreign_country = request.form.get('foreign_country', petition.foreign_country)
    petition.education_qualification = request.form.get('education_qualification', petition.education_qualification)
    
    # Employment Information
    petition.job_title = request.form.get('job_title', petition.job_title)
    petition.full_time = request.form.get('full_time', petition.full_time)
    petition.hours_per_week = request.form.get('hours_per_week')
    petition.wage_amount = request.form.get('wage_amount', petition.wage_amount)
    petition.wage_period = request.form.get('wage_period', petition.wage_period)
    petition.work_street_1 = request.form.get('work_street_1', petition.work_street_1)
    petition.work_apt_1 = request.form.get('work_apt_1')
    petition.work_city_1 = request.form.get('work_city_1', petition.work_city_1)
    petition.work_state_1 = request.form.get('work_state_1', petition.work_state_1)
    petition.work_zip_1 = request.form.get('work_zip_1', petition.work_zip_1)
    petition.itinerary = request.form.get('itinerary', petition.itinerary)
    petition.work_offsite = request.form.get('work_offsite', petition.work_offsite)
    
    # In a real application, we would commit changes to the database
    # db.session.commit()
    
    flash('I-129 form updated successfully', 'success')
    return redirect(url_for('attorney_i129_form', petition_id=petition_id))

@app.route('/attorney/update-i140/<int:petition_id>', methods=['POST'])
@attorney_required
def update_i140_petition(petition_id):
    petition = Petition.query.get(petition_id)
    
    if not petition:
        flash('Petition not found', 'error')
        return redirect(url_for('admin'))
    
    # Update petition fields from form data
    # Basic Information
    petition.alien_number = request.form.get('alien_number', petition.alien_number)
    petition.uscis_account = request.form.get('uscis_account', petition.uscis_account)
    petition.ssn = request.form.get('ssn', petition.ssn)
    petition.beneficiary_family_name = request.form.get('beneficiary_family_name', petition.beneficiary_family_name)
    petition.beneficiary_given_name = request.form.get('beneficiary_given_name', petition.beneficiary_given_name)
    petition.beneficiary_middle_name = request.form.get('beneficiary_middle_name', petition.beneficiary_middle_name)
    
    # Other Names
    other_names_used = request.form.get('other_names_used')
    if other_names_used == 'yes':
        petition.other_family_name = request.form.get('other_family_name', petition.other_family_name)
        petition.other_given_name = request.form.get('other_given_name', petition.other_given_name)
    else:
        petition.other_family_name = None
        petition.other_given_name = None
    
    # Personal Information
    petition.birth_date = request.form.get('birth_date', petition.birth_date)
    petition.gender = request.form.get('gender', petition.gender)
    petition.city_of_birth = request.form.get('city_of_birth', petition.city_of_birth)
    petition.country_of_birth = request.form.get('country_of_birth', petition.country_of_birth)
    petition.country_of_citizenship = request.form.get('country_of_citizenship', petition.country_of_citizenship)
    petition.marital_status = request.form.get('marital_status', petition.marital_status)
    
    # Application Type
    petition.adjustment_category = request.form.get('application_type', petition.adjustment_category)
    petition.receipt_number = request.form.get('receipt_number', petition.receipt_number)
    petition.priority_date = request.form.get('priority_date', petition.priority_date)
    
    # Travel Information
    petition.last_arrival_date = request.form.get('last_arrival_date', petition.last_arrival_date)
    petition.i94_number = request.form.get('i94_number', petition.i94_number)
    petition.current_status = request.form.get('current_status', petition.current_status)
    petition.status_expires = request.form.get('status_expires', petition.status_expires)
    petition.passport_number = request.form.get('passport_number', petition.passport_number)
    petition.passport_expiry_date = request.form.get('passport_expiry_date', petition.passport_expiry_date)
    
    # Address Information
    petition.current_address = request.form.get('current_address', petition.current_address)
    petition.current_apt = request.form.get('current_apt', petition.current_apt)
    petition.current_city = request.form.get('current_city', petition.current_city)
    petition.current_state = request.form.get('current_state', petition.current_state)
    petition.current_zip = request.form.get('current_zip', petition.current_zip)
    
    # Check if mailing address is different
    if not request.form.get('same_address'):
        petition.mailing_address = request.form.get('mailing_address', petition.mailing_address)
        petition.mailing_apt = request.form.get('mailing_apt', petition.mailing_apt)
        petition.mailing_city = request.form.get('mailing_city', petition.mailing_city)
        petition.mailing_state = request.form.get('mailing_state', petition.mailing_state)
        petition.mailing_zip = request.form.get('mailing_zip', petition.mailing_zip)
    else:
        # If same address is checked, copy current address to mailing address
        petition.mailing_address = petition.current_address
        petition.mailing_apt = petition.current_apt
        petition.mailing_city = petition.current_city
        petition.mailing_state = petition.current_state
        petition.mailing_zip = petition.current_zip
    
    # In a real application, we would commit changes to the database
    # db.session.commit()
    
    flash('I-140 form updated successfully', 'success')
    return redirect(url_for('attorney_i140_form', petition_id=petition_id))

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    return render_template('Admin.html', users=users)

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot delete yourself'})
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/attorney')
@login_required
@attorney_required
def attorney():
    # Get all petitions with their associated users for the attorney dashboard
    # Sort by created_at in descending order (newest first)
    petitions = Petition.query.join(User, Petition.user_id == User.id).order_by(Petition.created_at.desc()).all()
    
    # Add completion percentage and eligibility status for each petition
    for petition in petitions:
        # Calculate completion percentage based on filled fields
        filled_fields = 0
        total_fields = 0
        for column in petition.__table__.columns:
            if column.name != 'id' and column.name != 'user_id' and column.name != 'created_at' and column.name != 'updated_at':
                total_fields += 1
                if getattr(petition, column.name) is not None and getattr(petition, column.name) != '':
                    filled_fields += 1
        
        petition.completion_percentage = int((filled_fields / total_fields) * 100) if total_fields > 0 else 0
        
        # Determine eligibility based on completion percentage
        petition.is_eligible = petition.completion_percentage >= 90
        
        # Set state based on completion percentage if not already set
        if not hasattr(petition, 'state') or not petition.state or petition.state == '':
            if petition.completion_percentage == 100:
                petition.state = 'Approved'
            elif petition.completion_percentage >= 90:
                petition.state = 'Under Review'
            elif petition.completion_percentage >= 50:
                petition.state = 'Pending'
            else:
                petition.state = 'Needs Information'
        
        # Add user information to each petition for display
        petition.petitioner_name = f"{petition.user.firstname} {petition.user.lastname}"
        petition.petitioner_email = petition.user.email
        petition.petitioner_phone = petition.user.phone
    
    # Pass the petitions, page_size and current datetime to the attorney dashboard template
    return render_template('attorney_dashboard.html', petitions=petitions, now=datetime.now(), page_size=5)

@app.route('/attorney/petition/<int:petition_id>')
@login_required
@attorney_required
def attorney_view_petition(petition_id):
    # Get the petition with the specified ID
    petition = Petition.query.get_or_404(petition_id)
    
    # Get the associated user information
    user = User.query.get(petition.user_id)
    
    # Calculate completion percentage
    filled_fields = 0
    total_fields = 0
    for column in petition.__table__.columns:
        if column.name != 'id' and column.name != 'user_id' and column.name != 'created_at' and column.name != 'updated_at':
            total_fields += 1
            if getattr(petition, column.name) is not None and getattr(petition, column.name) != '':
                filled_fields += 1
    
    completion_percentage = int((filled_fields / total_fields) * 100) if total_fields > 0 else 0
    
    # Determine eligibility
    is_eligible = completion_percentage >= 90
    
    # Determine state if not set
    if not hasattr(petition, 'state') or not petition.state or petition.state == '':
        if completion_percentage == 100:
            state = 'Approved'
        elif completion_percentage >= 90:
            state = 'Under Review'
        elif completion_percentage >= 50:
            state = 'Pending'
        else:
            state = 'Needs Information'
    else:
        state = petition.state
    
    return render_template('attorney_review_form.html', 
                          petition=petition,
                          user=user,
                          completion_percentage=completion_percentage,
                          is_eligible=is_eligible,
                          state=state)

@app.route('/attorney/cases')
@login_required
@attorney_required
def attorney_cases():
    # Simulate active cases
    active_cases = []
    for i in range(1, 8):
        case_types = ['H-1B', 'Green Card', 'PERM', 'L-1', 'O-1', 'I-130', 'I-485']
        statuses = ['Initial Review', 'Request for Evidence', 'Preparing Documents', 'Ready for Filing', 'Filed']
        
        active_cases.append({
            'id': i,
            'client_name': f'Client {i}',
            'visa_type': case_types[i-1],
            'status': statuses[i % len(statuses)],
            'priority_date': f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
            'last_updated': f'{i} days ago'
        })
    
    # Simulate archived cases
    archived_cases = []
    for i in range(8, 12):
        case_types = ['H-1B', 'Green Card', 'PERM', 'L-1']
        outcomes = ['Approved', 'Denied', 'Withdrawn', 'Approved']
        
        archived_cases.append({
            'id': i,
            'client_name': f'Client {i}',
            'visa_type': case_types[i % len(case_types)],
            'outcome': outcomes[i % len(outcomes)],
            'close_date': f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
            'notes': 'Case completed successfully' if 'Approved' in outcomes[i % len(outcomes)] else 'Case unsuccessful'
        })
    
    return render_template('attorney_cases.html', 
                          active_cases=active_cases,
                          archived_cases=archived_cases)

@app.route('/attorney/add-feedback/<int:petition_id>', methods=['POST'])
@login_required
@attorney_required
def attorney_add_feedback(petition_id):
    # Get the petition with the specified ID
    petition = Petition.query.get_or_404(petition_id)
    
    # Get feedback from form submission
    feedback = request.form.get('feedback')
    feedback_type = request.form.get('feedback_type', 'general')  # general, document, form, etc.
    
    if feedback:
        # In a real application, you would save this to a Feedback model
        # For now, we'll just flash a message to simulate success
        flash(f'Feedback added successfully to petition #{petition_id}', 'success')
    else:
        flash('Feedback cannot be empty', 'error')
    
    # Redirect back to the petition details page
    return redirect(url_for('attorney_review_petition', petition_id=petition_id))

@app.route('/attorney/clients')
@login_required
@attorney_required
def attorney_clients():
    # Get page parameter from query string, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Simulate client list
    all_clients = []
    for i in range(1, 20):  # Create more clients to demonstrate pagination
        status = 'Active' if i % 3 != 0 else 'Inactive'
        all_clients.append({
            'id': i,
            'firstname': f'First{i}',
            'lastname': f'Last{i}',
            'email': f'client{i}@example.com',
            'phone': f'555-000-{1000+i}',
            'status': status,
            'cases': [{'id': j, 'type': 'Case Type'} for j in range(1, i % 3 + 2)],
            'join_date': f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
            'notes': f'Client notes for client {i}\nMultiple lines of notes\nShowing nl2br filter'
        })
    
    # Pagination logic
    items_per_page = 10
    total_clients = len(all_clients)
    
    # Calculate start and end indices for the current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_clients)
    
    # Get clients for the current page
    clients = all_clients[start_idx:end_idx]
    
    # Determine if there are more pages
    has_next = end_idx < total_clients
    
    return render_template('attorney_clients.html', 
                           clients=clients, 
                           page=page,
                           total_clients=total_clients,
                           has_next=has_next)

@app.route('/attorney/forms')
@login_required
@attorney_required
def attorney_forms():
    # Simulate immigration forms
    form_categories = {
        'Employment-Based': [
            {'id': 'I-129', 'name': 'Petition for Nonimmigrant Worker', 'description': 'For H-1B, L, O, and other employment-based temporary visas', 'last_updated': '2023-03-15'},
            {'id': 'I-140', 'name': 'Immigrant Petition for Alien Worker', 'description': 'For employment-based green cards', 'last_updated': '2025-06-04', 'fillable': True},
            {'id': 'ETA-9089', 'name': 'PERM Labor Certification', 'description': 'Required for many employment-based green cards', 'last_updated': '2023-05-01'}
        ],
        'Family-Based': [
            {'id': 'I-130', 'name': 'Petition for Alien Relative', 'description': 'For family-based immigration', 'last_updated': '2023-02-28'},
            {'id': 'I-485', 'name': 'Application to Register Permanent Residence', 'description': 'Adjustment of status to permanent resident', 'last_updated': '2023-04-10'},
            {'id': 'I-751', 'name': 'Petition to Remove Conditions on Residence', 'description': 'For conditional permanent residents through marriage', 'last_updated': '2023-03-15'}
        ],
        'Citizenship': [
            {'id': 'N-400', 'name': 'Application for Naturalization', 'description': 'For U.S. citizenship', 'last_updated': '2023-01-05'},
            {'id': 'N-600', 'name': 'Application for Certificate of Citizenship', 'description': 'For claiming citizenship through parents', 'last_updated': '2022-11-30'}
        ],
        'Humanitarian': [
            {'id': 'I-589', 'name': 'Application for Asylum and Withholding of Removal', 'description': 'For asylum seekers', 'last_updated': '2023-04-22'},
            {'id': 'I-918', 'name': 'Petition for U Nonimmigrant Status', 'description': 'For victims of crimes', 'last_updated': '2022-12-15'}
        ]
    }
    
    # Create detailed immigration forms list for the template
    immigration_forms = [
        {
            'id': 1,
            'code': 'I-129',
            'name': 'Petition for Nonimmigrant Worker',
            'category': 'employment',
            'description': 'Used by employers or sponsors to file for temporary foreign workers in nonimmigrant classifications such as H-1B, L-1, O-1, etc.',
            'edition_date': '07/20/2023',
            'expiration_date': '07/31/2025',
            'fee': '460',
            'pages': 9,
            'processing_time': '2-6 months',
            'supporting_documents': [
                'Labor Condition Application (for H-1B)',
                'Evidence of beneficiary qualifications',
                'Employer supporting documents',
                'Filing fee payment'
            ],
            'filing_location': 'USCIS Service Center based on classification and work location',
            'pdf_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-129.pdf',
            'instructions_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-129instr.pdf',
            'fillable': False
        },
        {
            'id': 2,
            'code': 'I-140',
            'name': 'Immigrant Petition for Alien Worker',
            'category': 'employment',
            'description': 'Used by employers to petition for foreign nationals to immigrate permanently to the United States based on employment.',
            'edition_date': '01/31/2024',
            'expiration_date': '01/31/2026',
            'fee': '700',
            'pages': 9,
            'processing_time': '3-8 months',
            'supporting_documents': [
                'Labor certification (if required)',
                'Evidence of ability to pay wage',
                'Evidence of beneficiary qualifications',
                'Filing fee payment'
            ],
            'filing_location': 'USCIS Service Center based on classification and employer location',
            'pdf_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-140.pdf',
            'instructions_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-140instr.pdf',
            'fillable': True
        },
        {
            'id': 3,
            'code': 'I-485',
            'name': 'Application to Register Permanent Residence or Adjust Status',
            'category': 'adjustment',
            'description': 'Used by individuals already in the United States to apply for lawful permanent resident status.',
            'edition_date': '12/01/2023',
            'expiration_date': '12/31/2025',
            'fee': '1225',
            'pages': 20,
            'processing_time': '8-14 months',
            'supporting_documents': [
                'Form I-797 approval notice (if applicable)',
                'Birth certificate',
                'Passport photos',
                'Medical examination (Form I-693)'
            ],
            'filing_location': 'USCIS Lockbox facility based on eligibility category and residence',
            'pdf_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-485.pdf',
            'instructions_url': 'https://www.uscis.gov/sites/default/files/document/forms/i-485instr.pdf',
            'fillable': False
        }
    ]
    
    return render_template('attorney_forms.html', form_categories=form_categories, immigration_forms=immigration_forms)

@app.route('/attorney/documents')
@login_required
@attorney_required
def attorney_documents():
    # Simulate clients for document filtering
    clients = []
    for i in range(1, 10):
        clients.append({
            'id': i,
            'name': f'Client {i}'
        })
    
    # Simulate documents
    documents = []
    doc_types = ['Passport', 'Birth Certificate', 'Marriage Certificate', 'Employment Letter', 
                'Academic Transcript', 'Tax Return', 'I-94 Record', 'Previous Visa']
    
    for i in range(1, 20):
        doc_type = doc_types[i % len(doc_types)]
        client_id = (i % 9) + 1
        
        documents.append({
            'id': i,
            'name': f'{doc_type} - Client {client_id}',
            'type': doc_type,
            'client_id': client_id,
            'client_name': f'Client {client_id}',
            'upload_date': f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
            'size': (i % 10) + 1,
            'size_formatted': f'{(i % 10) + 1} MB',
            'icon': get_document_icon(doc_type),
            'case_id': i if i % 4 == 0 else None,
            'shared': (i % 3 == 0)
        })
    
    return render_template('attorney_documents.html', documents=documents, clients=clients)


@app.route('/attorney/upload-document', methods=['POST'])
@login_required
@attorney_required
def upload_attorney_document():
    # In a real application, handle file upload with request.files
    # For this simulation, we'll just return a success response
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '')
        document_type = request.form.get('type', 'other')
        client_id = request.form.get('client_id', '')
        case_id = request.form.get('case_id', '')
        
        # Simulate file upload processing
        # In a real app, you would save the file and store metadata in the database
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Document "{name}" uploaded successfully',
            'document': {
                'id': 999,  # Simulated new document ID
                'name': name,
                'type': document_type,
                'client_id': int(client_id) if client_id.isdigit() else None,
                'client_name': f'Client {client_id}' if client_id.isdigit() else 'No Client',
                'case_id': int(case_id) if case_id.isdigit() else None,
                'upload_date': datetime.now().strftime('%Y-%m-%d'),
                'size_formatted': '2.5 MB',  # Simulated file size
                'icon': get_document_icon(document_type),
                'shared': False
            }
        })


@app.route('/petition/<int:petition_id>', endpoint='attorney_petition_details')
@login_required
@attorney_required
def petition_details(petition_id):
    # Simulate petition data
    petition = {
        'id': petition_id,
        'type': 'H-1B Visa',
        'status': 'Under Review',
        'priority_date': '2023-05-15',
        'completion_percentage': 65,
        'petitioner': {
            'name': 'ABC Tech Corporation',
            'contact': 'John Smith',
            'email': 'jsmith@abctech.com',
            'phone': '555-123-4567',
            'address': '123 Corporate Way, San Francisco, CA 94107'
        },
        'beneficiary': {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '555-987-6543',
            'nationality': 'India',
            'current_status': 'F-1 Student',
            'address': '456 University Ave, Palo Alto, CA 94301'
        },
        'position': {
            'title': 'Senior Software Engineer',
            'duties': 'Design and develop software applications, lead technical projects, mentor junior developers.',
            'requirements': 'Master\'s degree in Computer Science or related field, 5+ years experience in software development.',
            'salary': '$150,000 per year',
            'location': 'San Francisco, CA'
        },
        'timeline': [
            {'date': '2023-05-15', 'event': 'Petition filed', 'status': 'complete'},
            {'date': '2023-05-20', 'event': 'Initial review', 'status': 'complete'},
            {'date': '2023-06-10', 'event': 'RFE received', 'status': 'complete'},
            {'date': '2023-06-25', 'event': 'RFE response submitted', 'status': 'complete'},
            {'date': '2023-07-15', 'event': 'Final review', 'status': 'in-progress'},
            {'date': 'Pending', 'event': 'Decision', 'status': 'pending'}
        ],
        'documents': [
            {'name': 'Form I-129', 'status': 'submitted', 'date': '2023-05-15'},
            {'name': 'Labor Condition Application', 'status': 'submitted', 'date': '2023-05-15'},
            {'name': 'Employer Support Letter', 'status': 'submitted', 'date': '2023-05-15'},
            {'name': 'Beneficiary Resume', 'status': 'submitted', 'date': '2023-05-15'},
            {'name': 'Educational Credentials', 'status': 'submitted', 'date': '2023-05-15'},
            {'name': 'RFE Response', 'status': 'submitted', 'date': '2023-06-25'}
        ],
        'notes': 'Client has requested expedited processing. Beneficiary\'s current status expires in 3 months.\nRFE requested additional evidence of specialized knowledge.'
    }
    
    return render_template('petition_details.html', petition=petition)

@app.route('/attorney/review-petition/<int:petition_id>')
@login_required
def attorney_review_petition(petition_id):
    # Fetch petition data from database
    petition_data = Petition.query.get_or_404(petition_id)
    
    # Get the user associated with this petition
    user = User.query.get(petition_data.user_id) if petition_data.user_id else None
    
    # Format the petition data for the template
    petition = {
        'id': petition_data.id,
        'first_name': petition_data.petitioner_given_name,
        'last_name': petition_data.petitioner_family_name,
        'email': petition_data.email,
        'phone': petition_data.daytime_phone,
        'submission_date': petition_data.created_at.strftime('%Y-%m-%d') if petition_data.created_at else 'N/A',
        'form_type': 'I-129 Petition',  # Hardcoded for now, could be stored in a separate field
        'completion_percentage': 85,  # Placeholder, would be calculated based on form completeness
        'is_eligible': True,  # This would be determined by business logic
        'state': petition_data.state or 'Under Review',
        'admin_notes': '',
        'has_mismatches': False,  # Will be updated based on field matches
        'mismatch_fields': []  # Will store IDs of mismatched fields
    }
    
    # Get form data from the petition_data JSON field
    form_data = {}
    if petition_data.form_data:
        try:
            import json
            form_data = json.loads(petition_data.form_data)
        except:
            form_data = {}
    
    # Build form sections based on form type
    petition['form_sections'] = []
    
    # Personal Information section
    personal_info = {
        'title': 'Personal Information',
        'fields': [
            {'id': 'name', 'label': 'Full Name', 'value': f"{petition['first_name']} {petition['last_name']}"},
            {'id': 'email', 'label': 'Email', 'value': petition['email']},
            {'id': 'phone', 'label': 'Phone', 'value': petition['phone']}
        ]
    }
    
    # Add additional fields from form_data
    if form_data.get('personal_info'):
        for key, value in form_data.get('personal_info', {}).items():
            if key not in ['first_name', 'last_name', 'email', 'phone']:
                personal_info['fields'].append({
                    'id': key,
                    'label': key.replace('_', ' ').title(),
                    'value': value
                })
    
    petition['form_sections'].append(personal_info)
    
    # Employment Details section (for I-140 and I-129)
    if petition['form_type'] in ['I-140', 'I-129'] and form_data.get('employment'):
        employment_info = {
            'title': 'Employment Details',
            'fields': []
        }
        
        for key, value in form_data.get('employment', {}).items():
            employment_info['fields'].append({
                'id': key,
                'label': key.replace('_', ' ').title(),
                'value': value
            })
        
        petition['form_sections'].append(employment_info)
    
    # Add other form sections based on form_data
    for section_key, section_data in form_data.items():
        if section_key not in ['personal_info', 'employment'] and isinstance(section_data, dict):
            section = {
                'title': section_key.replace('_', ' ').title(),
                'fields': []
            }
            
            for key, value in section_data.items():
                section['fields'].append({
                    'id': key,
                    'label': key.replace('_', ' ').title(),
                    'value': value
                })
            
            petition['form_sections'].append(section)
    
    # Get documents associated with this petition
    # In a real app, you would query the database for documents
    # For now, we'll create sample documents
    petition['documents'] = [
        {
            'id': 1,
            'name': 'Passport.pdf',
            'type': 'Identification',
            'icon': 'fa-passport',
            'upload_date': '2023-05-10'
        },
        {
            'id': 2,
            'name': 'Resume.pdf',
            'type': 'Professional',
            'icon': 'fa-file-alt',
            'upload_date': '2023-05-10'
        },
        {
            'id': 3,
            'name': 'Birth_Certificate.pdf',
            'type': 'Identification',
            'icon': 'fa-id-card',
            'upload_date': '2023-05-12'
        },
        {
            'id': 4,
            'name': 'Employment_Letter.pdf',
            'type': 'Employment',
            'icon': 'fa-file-contract',
            'upload_date': '2023-05-15'
        }
    ]
    
    # Get feedback history for this petition
    # In a real app, you would query the database for feedback entries
    petition['feedback_history'] = []
    if petition_data.feedback:
        try:
            feedback_list = json.loads(petition_data.feedback)
            for feedback in feedback_list:
                petition['feedback_history'].append({
                    'date': feedback.get('date', 'N/A'),
                    'admin': feedback.get('admin', 'Unknown'),
                    'content': feedback.get('content', '')
                })
        except:
            pass
    
    # Field Matching Details
    # This would normally be determined by comparing form data with document data
    # For now, we'll create sample field matches
    petition['field_matches'] = [
        {
            'field_name': 'Full Name',
            'matches': True,
            'form_value': f"{petition_data.petitioner_given_name} {petition_data.petitioner_family_name}",
            'doc_value': f"{petition_data.petitioner_given_name} {petition_data.petitioner_family_name}"
        },
        {
            'field_name': 'Date of Birth',
            'matches': True,
            'form_value': petition_data.birth_date.strftime('%Y-%m-%d') if hasattr(petition_data, 'birth_date') and petition_data.birth_date else 'N/A',
            'doc_value': petition_data.birth_date.strftime('%Y-%m-%d') if hasattr(petition_data, 'birth_date') and petition_data.birth_date else 'N/A'
        },
        {
            'field_name': 'Passport Number',
            'matches': True,
            'form_value': petition_data.passport_number if hasattr(petition_data, 'passport_number') else 'N/A',
            'doc_value': petition_data.passport_number if hasattr(petition_data, 'passport_number') else 'N/A'
        },
        {
            'field_name': 'Country of Birth',
            'matches': False,
            'form_value': petition_data.country_of_birth if hasattr(petition_data, 'country_of_birth') else 'United States',
            'doc_value': 'Canada'
        },
        {
            'field_name': 'Alien Registration Number',
            'matches': False,
            'form_value': petition_data.alien_number if hasattr(petition_data, 'alien_number') else 'A123456789',
            'doc_value': 'A987654321'
        }
    ]
    
    # Update has_mismatches flag based on field matches
    for field_match in petition['field_matches']:
        if not field_match['matches']:
            petition['has_mismatches'] = True
            petition['mismatch_fields'].append(field_match['field_name'].lower().replace(' ', '_'))
    
    return render_template('attorney_review_form.html', petition=petition, state=petition['state'])

@app.route('/attorney/update-petition-status/<int:petition_id>', methods=['POST'])
@login_required
def attorney_update_petition_status(petition_id):
    # Get the petition from the database
    petition = Petition.query.get_or_404(petition_id)
    
    if request.method == 'POST':
        status = request.form.get('status', '')
        notes = request.form.get('notes', '')
        
        # Validate inputs
        if not status:
            flash('Status is required', 'error')
            return redirect(url_for('attorney_review_petition', petition_id=petition_id))
        
        # Update the petition status in the database
        petition.state = status
        
        # Add notes if provided
        if notes:
            petition.admin_notes = notes
        
        # Add to feedback history
        import json
        from datetime import datetime
        
        # Get current attorney name from session
        attorney_name = session.get('attorney_name', session.get('admin_name', 'Unknown Attorney'))
        
        # Create new feedback entry
        new_feedback = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'admin': attorney_name,
            'content': notes if notes else f'Status updated to {status}'
        }
        
        # Update feedback history in the petition
        feedback_list = []
        if petition.feedback:
            try:
                feedback_list = json.loads(petition.feedback)
                if not isinstance(feedback_list, list):
                    feedback_list = []
            except:
                feedback_list = []
        
        feedback_list.append(new_feedback)
        petition.feedback = json.dumps(feedback_list)
        
        # Save changes to database
        db.session.commit()
        
        # Log the action
        print(f"Petition {petition_id} status updated to {status} by attorney {attorney_name}")
        print(f"Notes: {notes}")
        
        flash(f'Petition status updated to {status}', 'success')
        return redirect(url_for('attorney'))

@app.route('/attorney/save-feedback/<int:petition_id>', methods=['POST'])
@login_required
def attorney_save_feedback(petition_id):
    # Get the petition from the database
    petition = Petition.query.get_or_404(petition_id)
    
    if request.method == 'POST':
        notes = request.form.get('notes', '')
        
        # Validate inputs
        if not notes:
            flash('Feedback content is required', 'error')
            return redirect(url_for('attorney_review_petition', petition_id=petition_id))
        
        # Add to feedback history
        import json
        from datetime import datetime
        
        # Get current attorney name from session
        attorney_name = session.get('attorney_name', session.get('admin_name', 'Unknown Attorney'))
        
        # Create new feedback entry
        new_feedback = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'admin': attorney_name,
            'content': notes
        }
        
        # Update feedback history in the petition
        feedback_list = []
        if petition.feedback:
            try:
                feedback_list = json.loads(petition.feedback)
                if not isinstance(feedback_list, list):
                    feedback_list = []
            except:
                feedback_list = []
        
        feedback_list.append(new_feedback)
        petition.feedback = json.dumps(feedback_list)
        
        # Save changes to database
        db.session.commit()
        
        # Log the action
        print(f"Feedback added to petition {petition_id} by attorney {attorney_name}")
        print(f"Feedback: {notes}")
        
        flash('Feedback saved successfully', 'success')
        return redirect(url_for('attorney_review_petition', petition_id=petition_id))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get the current user's petitions
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your dashboard', 'error')
        return redirect(url_for('login'))
    
    # Query all petitions for this user
    user_petitions = Petition.query.filter_by(user_id=user_id).all()
    
    return render_template('dashboard.html', user_petitions=user_petitions)

@app.route('/user/petitions')
@login_required
def user_petitions():
    # Get the current user's petitions
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your petitions', 'error')
        return redirect(url_for('login'))
    
    # Query all petitions for this user
    user_petitions = Petition.query.filter_by(user_id=user_id).all()
    
    # Get current time for the last updated timestamp
    now = datetime.now()
    
    return render_template('my_petitions.html', user_petitions=user_petitions, now=now)

@app.route('/user/petition/<int:petition_id>')
@login_required
def user_view_petition(petition_id):
    # Get the petition from the database
    petition_data = Petition.query.get_or_404(petition_id)
    
    # Make sure the user owns this petition
    if petition_data.user_id != session.get('user_id'):
        flash('You do not have permission to view this petition', 'error')
        return redirect(url_for('dashboard'))
    
    # Format the petition data for the template
    petition = {
        'id': petition_data.id,
        'first_name': petition_data.petitioner_given_name,
        'last_name': petition_data.petitioner_family_name,
        'email': petition_data.email,
        'phone': petition_data.daytime_phone,
        'submission_date': petition_data.created_at.strftime('%Y-%m-%d') if petition_data.created_at else 'N/A',
        'form_type': 'I-129 Petition',  # Hardcoded for now
        'status': petition_data.state or 'Under Review',
        'completion_percentage': 85,  # Placeholder
        'admin_notes': petition_data.admin_notes or ''
    }
    
    # Get feedback history for this petition
    petition['feedback_history'] = []
    if petition_data.feedback:
        try:
            import json
            feedback_list = json.loads(petition_data.feedback)
            for feedback in feedback_list:
                petition['feedback_history'].append({
                    'date': feedback.get('date', 'N/A'),
                    'admin': feedback.get('admin', 'Unknown'),
                    'content': feedback.get('content', '')
                })
        except:
            pass
    
    return render_template('user_petition_view.html', petition=petition)
    
    return redirect(url_for('attorney_review_petition', petition_id=petition_id))

@app.route('/attorney/calendar')
@login_required
@attorney_required
def attorney_calendar():
    import datetime
    
    # Current date for generating events
    now = datetime.datetime.now()
    
    # Simulate clients
    clients = []
    for i in range(1, 10):
        clients.append({
            'id': i,
            'firstname': f'First{i}',
            'lastname': f'Last{i}'
        })
    
    # Simulate calendar events
    calendar_events = []
    event_types = ['appointment', 'deadline', 'court', 'consultation', 'reminder']
    event_colors = {
        'appointment': '#4299e1',
        'deadline': '#f56565',
        'court': '#805ad5',
        'consultation': '#38a169',
        'reminder': '#ecc94b',
        'other': '#a0aec0'
    }
    
    # Generate events for the next 30 days
    for i in range(1, 20):
        event_type = event_types[i % len(event_types)]
        event_date = now + datetime.timedelta(days=i % 30)
        client_id = (i % 9) + 1 if i % 3 == 0 else None
        
        event = {
            'id': i,
            'title': f'{event_type.capitalize()} {i}',
            'start': event_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': (event_date + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'color': event_colors[event_type],
            'eventType': event_type,
            'description': f'Description for {event_type} {i}'
        }
        
        if client_id:
            event['clientName'] = f'Client {client_id}'
            event['clientId'] = client_id
            
            # Sometimes add a case ID
            if i % 5 == 0:
                event['caseId'] = i + 100
        
        if i % 4 == 0:
            event['location'] = 'Office' if i % 2 == 0 else 'Video Conference'
            
        calendar_events.append(event)
    
    # Upcoming events (next 5 events)
    upcoming_events = []
    for i in range(1, 6):
        event_date = now + datetime.timedelta(days=i, hours=i)
        event_type = event_types[i % len(event_types)]
        client_id = (i % 9) + 1 if i % 2 == 0 else None
        
        event = {
            'id': i + 100,
            'title': f'{event_type.capitalize()} with Client {client_id}' if client_id else f'{event_type.capitalize()} {i}',
            'start_time': event_date,
            'end_time': event_date + datetime.timedelta(hours=1),
            'color': event_colors[event_type]
        }
        
        if client_id:
            event['client_name'] = f'Client {client_id}'
            
        upcoming_events.append(event)
    
    return render_template('attorney_calendar.html', 
                          calendar_events=calendar_events,
                          upcoming_events=upcoming_events,
                          clients=clients)

@app.route('/attorney/settings')
@login_required
@attorney_required
def attorney_settings():
    # Get current user
    user_id = session.get('user_id')
    attorney = User.query.get(user_id)
    
    # Simulate attorney preferences
    if not hasattr(attorney, 'preferences'):
        attorney.preferences = {
            'theme': 'light',
            'dashboard_layout': 'detailed',
            'default_calendar_view': 'month'
        }
    
    # Simulate notification settings
    if not hasattr(attorney, 'notifications'):
        attorney.notifications = {
            'email_new_cases': True,
            'email_case_updates': True,
            'email_deadlines': True,
            'email_appointments': True,
            'system_messages': True,
            'system_client_messages': True
        }
    
    # Simulate two-factor authentication status
    if not hasattr(attorney, 'two_factor_enabled'):
        attorney.two_factor_enabled = False
    
    # For demonstration purposes
    attorney.bar_number = 'ABC12345'
    attorney.jurisdiction = 'New York State'
    attorney.practice_areas = ['family', 'employment']
    attorney.bio = 'Experienced immigration attorney with 10+ years of practice.'
    
    return render_template('attorney_settings.html', attorney=attorney)

# API routes for attorney functions

@app.route('/attorney/get-client-cases/<int:client_id>')
@login_required
@attorney_required
def get_client_cases(client_id):
    # Simulate cases for the client
    cases = []
    case_types = ['H-1B', 'Green Card', 'PERM', 'L-1', 'O-1']
    
    for i in range(1, 4):
        cases.append({
            'id': client_id * 10 + i,
            'visa_type': case_types[i % len(case_types)],
            'status': 'Active'
        })
    
    return jsonify({'success': True, 'cases': cases})

@app.route('/attorney/add-client', methods=['POST'])
@login_required
@attorney_required
def add_client():
    # In a real application, validate and save to database
    return jsonify({'success': True, 'message': 'Client added successfully'})

@app.route('/attorney/edit-client/<int:client_id>', methods=['POST'])
@login_required
@attorney_required
def edit_client(client_id):
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Client updated successfully'})

@app.route('/attorney/toggle-client-status/<int:client_id>', methods=['POST'])
@login_required
@attorney_required
def toggle_client_status(client_id):
    # In a real application, update status in database
    return jsonify({'success': True, 'message': 'Client status updated'})

@app.route('/attorney/upload-document', methods=['POST'])
@login_required
@attorney_required
def upload_document():
    # In a real application, validate and save file to storage
    return jsonify({'success': True, 'message': 'Document uploaded successfully'})

@app.route('/attorney/share-document/<int:document_id>', methods=['POST'])
@login_required
@attorney_required
def share_document(document_id):
    # In a real application, update sharing settings in database
    return jsonify({'success': True, 'message': 'Document shared successfully'})

@app.route('/attorney/delete-document/<int:document_id>', methods=['POST'])
@login_required
@attorney_required
def delete_document(document_id):
    # In a real application, delete from storage and database
    return jsonify({'success': True, 'message': 'Document deleted successfully'})

@app.route('/attorney/add-calendar-event', methods=['POST'])
@login_required
@attorney_required
def add_calendar_event():
    # In a real application, validate and save to database
    return jsonify({'success': True, 'message': 'Event added successfully'})

@app.route('/attorney/edit-event/<int:event_id>', methods=['POST'])
@login_required
@attorney_required
def edit_calendar_event(event_id):
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Event updated successfully'})

@app.route('/attorney/delete-event/<int:event_id>', methods=['POST'])
@login_required
@attorney_required
def delete_calendar_event(event_id):
    # In a real application, delete from database
    return jsonify({'success': True, 'message': 'Event deleted successfully'})

@app.route('/attorney/update-attorney-profile', methods=['POST'])
@login_required
@attorney_required
def update_attorney_profile():
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/attorney/update-attorney-password', methods=['POST'])
@login_required
@attorney_required
def update_attorney_password():
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/attorney/update-attorney-notifications', methods=['POST'])
@login_required
@attorney_required
def update_attorney_notifications():
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Notification preferences updated'})

@app.route('/attorney/update-attorney-preferences', methods=['POST'])
@login_required
@attorney_required
def update_attorney_preferences():
    # In a real application, validate and update database
    return jsonify({'success': True, 'message': 'Preferences updated successfully'})

@app.route('/attorney/enable-two-factor', methods=['POST'])
@login_required
@attorney_required
def enable_two_factor():
    # In a real application, validate code and enable 2FA
    return jsonify({'success': True, 'message': 'Two-factor authentication enabled'})

@app.route('/attorney/disable-two-factor', methods=['POST'])
@login_required
@attorney_required
def disable_two_factor():
    # In a real application, validate password and disable 2FA
    return jsonify({'success': True, 'message': 'Two-factor authentication disabled'})


@app.route('/attorney/petition/<int:petition_id>')
@login_required
@attorney_required
def petition_details(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    
    # Simulated data for petition progress
    import random
    progress_steps = [
        {'name': 'Initial Review', 'status': 'completed', 'date': '2025-05-15'},
        {'name': 'Document Collection', 'status': 'completed', 'date': '2025-05-20'},
        {'name': 'Form Preparation', 'status': 'in-progress', 'date': '2025-05-25'},
        {'name': 'Attorney Review', 'status': 'pending', 'date': ''},
        {'name': 'USCIS Submission', 'status': 'pending', 'date': ''},
        {'name': 'USCIS Processing', 'status': 'pending', 'date': ''},
        {'name': 'Decision', 'status': 'pending', 'date': ''}
    ]
    
    # Simulated document status
    documents = [
        {'name': 'Passport', 'status': 'submitted', 'date': '2025-05-16'},
        {'name': 'Resume/CV', 'status': 'submitted', 'date': '2025-05-17'},
        {'name': 'Educational Credentials', 'status': 'submitted', 'date': '2025-05-18'},
        {'name': 'Employment Verification Letter', 'status': 'missing', 'date': ''},
        {'name': 'Previous Visa Documentation', 'status': 'submitted', 'date': '2025-05-19'},
        {'name': 'I-129 Form', 'status': 'in-progress', 'date': '2025-05-25'}
    ]
    
    return render_template('petition_details.html', 
                          petition=petition,
                          progress_steps=progress_steps,
                          documents=documents)

@app.route('/attorney/submit-attorney-form', methods=['POST'])
@login_required
@attorney_required
def submit_attorney_form():
    # Process the attorney-filled form submission
    if request.method == 'POST':
        # Handle form data processing here
        petition_id = request.form.get('petition_id')
        form_type = request.form.get('form_type')
        
        # Save form data logic would go here
        
        flash('Form submitted successfully!', 'success')


@app.route("/api/user_petition", methods=["GET"])
def get_user_petition():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify(success=False, error="No user_id provided")

    petition = Petition.query.filter_by(user_id=user_id).first()
    if petition:
        return jsonify(success=True, petition=petition.to_dict())
    else:
        return jsonify(success=False, petition=None)

    # Handle POST request for saving partial form data
    if request.method == 'POST':
        try:
            # Get JSON data from request
            form_data = request.json
            if not form_data:
                form_data = request.form.to_dict()
                
            print(f"Received form data: {form_data}")
            
            print("\n" + "="*50)
            print("PARTIAL FORM SUBMISSION RECEIVED")
            print("="*50)
            print("Form data received:")
            for key, value in form_data.items():
                print(f"{key}: {value}")
            print("="*50 + "\n")
            
            # Get the user's email from either the form data or session
            user_email = form_data.get('email') or session.get('email')
            if not user_email and 'email' in session:
                user_email = session['email']
        except Exception as e:
            print(f"Error parsing form data: {str(e)}")
            return jsonify({'success': False, 'message': f'Error parsing form data: {str(e)}'}), 400
            
        try:
            # Use both user_id and email to locate existing petitions
            existing_petition = None
            if user_id:
                # First try by user ID
                existing_petition = Petition.query.filter_by(user_id=user_id).order_by(Petition.created_at.desc()).first()
                print(f"Looking for petition by user_id={user_id}: {'Found' if existing_petition else 'Not found'}")
                
                # If not found by user ID and we have the email, try by email
                if not existing_petition and user_email:
                    existing_petition = Petition.query.filter_by(email=user_email).order_by(Petition.created_at.desc()).first()
                    print(f"Looking for petition by email={user_email}: {'Found' if existing_petition else 'Not found'}")
                    # Update the user_id if found by email
                    if existing_petition:
                        print(f"Found petition by email {user_email}, updating its user_id to {user_id}")
                        existing_petition.user_id = user_id
            
            # Process dates if they exist
            birth_date = None
            if form_data.get('birthDate'):
                try:
                    birth_date = datetime.strptime(form_data['birthDate'], '%Y-%m-%d')
                except ValueError as e:
                    print(f"Error parsing birth date: {e}")
            
            passport_expiry_date = None
            if form_data.get('passportExpiryDate'):
                try:
                    passport_expiry_date = datetime.strptime(form_data['passportExpiryDate'], '%Y-%m-%d')
                except ValueError as e:
                    print(f"Error parsing passport expiry date: {e}")
            
            # If petition exists, update it
            if existing_petition:
                # Update petition with new data, only if the field exists in the form data
                # Part 1: Petitioner Information
                if 'petitionerFamilyName' in form_data:
                    existing_petition.petitioner_family_name = form_data['petitionerFamilyName']
                if 'petitionerGivenName' in form_data:
                    existing_petition.petitioner_given_name = form_data['petitionerGivenName']
                if 'petitionerMiddleName' in form_data:
                    existing_petition.petitioner_middle_name = form_data.get('petitionerMiddleName', '')
                if 'companyName' in form_data:
                    existing_petition.company_name = form_data['companyName']
                if 'inCareOf' in form_data:
                    existing_petition.in_care_of = form_data.get('inCareOf', '')
                if 'streetAddress' in form_data:
                    existing_petition.street_address = form_data.get('streetAddress', '')
                if 'aptSteFlr' in form_data:
                    existing_petition.apt_ste_flr = form_data.get('aptSteFlr', '')
                if 'city' in form_data:
                    existing_petition.city = form_data.get('city', '')
                if 'state' in form_data:
                    existing_petition.state = form_data.get('state', '')
                if 'zipCode' in form_data:
                    existing_petition.zip_code = form_data.get('zipCode', '')
                if 'province' in form_data:
                    existing_petition.province = form_data.get('province', '')
                if 'postalCode' in form_data:
                    existing_petition.postal_code = form_data.get('postalCode', '')
                if 'country' in form_data:
                    existing_petition.country = form_data.get('country', '')
                if 'daytimePhone' in form_data:
                    existing_petition.daytime_phone = form_data['daytimePhone']
                if 'mobilePhone' in form_data:
                    existing_petition.mobile_phone = form_data.get('mobilePhone', '')
                if 'email' in form_data:
                    existing_petition.email = form_data['email']
                if 'fein' in form_data:
                    existing_petition.fein = form_data['fein']
                
                # Part 2: Basis for Classification
                if 'basisForClassification' in form_data:
                    existing_petition.basis_for_classification = form_data['basisForClassification']
                
                # Part 3: Beneficiary Information
                if 'beneficiaryFamilyName' in form_data:
                    existing_petition.beneficiary_family_name = form_data['beneficiaryFamilyName']
                if 'beneficiaryGivenName' in form_data:
                    existing_petition.beneficiary_given_name = form_data['beneficiaryGivenName']
                if 'beneficiaryMiddleName' in form_data:
                    existing_petition.beneficiary_middle_name = form_data.get('beneficiaryMiddleName', '')
                if 'otherFamilyName' in form_data:
                    existing_petition.other_family_name = form_data.get('otherFamilyName', '')
                if 'otherGivenName' in form_data:
                    existing_petition.other_given_name = form_data.get('otherGivenName', '')
                if 'otherMiddleName' in form_data:
                    existing_petition.other_middle_name = form_data.get('otherMiddleName', '')
                if birth_date:
                    existing_petition.birth_date = birth_date
                if 'gender' in form_data:
                    existing_petition.gender = form_data.get('gender', '')
                if 'ssn' in form_data:
                    existing_petition.ssn = form_data.get('ssn', '')
                if 'alienNumber' in form_data:
                    existing_petition.alien_number = form_data.get('alienNumber', '')
                if 'countryOfBirth' in form_data:
                    existing_petition.country_of_birth = form_data['countryOfBirth']
                if 'countryOfCitizenship' in form_data:
                    existing_petition.country_of_citizenship = form_data['countryOfCitizenship']
                if 'passportNumber' in form_data:
                    existing_petition.passport_number = form_data['passportNumber']
                if passport_expiry_date:
                    existing_petition.passport_expiry_date = passport_expiry_date
                if 'educationQualification' in form_data:
                    existing_petition.education_qualification = form_data['educationQualification']
                
                # Part 4: Processing Information
                if 'foreignStreet' in form_data:
                    existing_petition.foreign_street = form_data.get('foreignStreet', '')
                if 'foreignApt' in form_data:
                    existing_petition.foreign_apt = form_data.get('foreignApt', '')
                if 'foreignCity' in form_data:
                    existing_petition.foreign_city = form_data.get('foreignCity', '')
                if 'foreignState' in form_data:
                    existing_petition.foreign_state = form_data.get('foreignState', '')
                if 'foreignPostal' in form_data:
                    existing_petition.foreign_postal = form_data.get('foreignPostal', '')
                if 'foreignCountry' in form_data:
                    existing_petition.foreign_country = form_data.get('foreignCountry', '')
                if 'validPassport' in form_data:
                    existing_petition.valid_passport = form_data.get('validPassport', '')
                if 'passportExplanation' in form_data:
                    existing_petition.passport_explanation = form_data.get('passportExplanation', '')
                
                # Part 5: Basic Information About Proposed Employment
                if 'jobTitle' in form_data:
                    existing_petition.job_title = form_data['jobTitle']
                if 'lcaNumber' in form_data:
                    existing_petition.lca_number = form_data['lcaNumber']
                if 'workStreet1' in form_data:
                    existing_petition.work_street_1 = form_data.get('workStreet1', '')
                if 'workApt1' in form_data:
                    existing_petition.work_apt_1 = form_data.get('workApt1', '')
                if 'workCity1' in form_data:
                    existing_petition.work_city_1 = form_data.get('workCity1', '')
                if 'workState1' in form_data:
                    existing_petition.work_state_1 = form_data.get('workState1', '')
                if 'workZip1' in form_data:
                    existing_petition.work_zip_1 = form_data.get('workZip1', '')
                if 'thirdParty1' in form_data:
                    existing_petition.third_party_1 = form_data.get('thirdParty1', 'no')
                if 'thirdPartyOrg1' in form_data:
                    existing_petition.third_party_org_1 = form_data.get('thirdPartyOrg1', '')
                if 'itinerary' in form_data:
                    existing_petition.itinerary = form_data.get('itinerary', 'no')
                if 'workOffsite' in form_data:
                    existing_petition.work_offsite = form_data.get('workOffsite', 'no')
                if 'fullTime' in form_data:
                    existing_petition.full_time = form_data.get('fullTime', 'yes')
                if 'hoursPerWeek' in form_data and form_data.get('hoursPerWeek'):
                    existing_petition.hours_per_week = int(form_data.get('hoursPerWeek'))
                if 'wageAmount' in form_data and form_data.get('wageAmount'):
                    existing_petition.wage_amount = float(form_data.get('wageAmount'))
                if 'wagePeriod' in form_data:
                    existing_petition.wage_period = form_data.get('wagePeriod', '')
                
                # Save changes to the existing petition
                db.session.commit()
                print(f"Updated existing petition {existing_petition.id} successfully")
                
                return jsonify({'success': True, 'message': 'Petition updated successfully', 'id': existing_petition.id})
            else:
                # Create a new petition with the form data
                print("Creating new petition")
                new_petition = Petition(
                    user_id=user_id,
                    email=user_email,
                    created_at=datetime.now()
                )
                
                # Add all the fields from form_data to the new petition
                # Copy fields from form_data to the new petition (just like we did for existing_petition)
                if 'petitionerFamilyName' in form_data:
                    new_petition.petitioner_family_name = form_data['petitionerFamilyName']
                if 'petitionerGivenName' in form_data:
                    new_petition.petitioner_given_name = form_data['petitionerGivenName']
                if 'petitionerMiddleName' in form_data:
                    new_petition.petitioner_middle_name = form_data.get('petitionerMiddleName', '')
                if 'companyName' in form_data:
                    new_petition.company_name = form_data['companyName']
                # Copy email field specifically to ensure it's saved
                if 'email' in form_data:
                    new_petition.email = form_data['email']
                
                # Add the new petition to the database
                db.session.add(new_petition)
                db.session.commit()
                print("Created new petition successfully")
                
                return jsonify({'success': True, 'message': 'Petition created successfully', 'id': new_petition.id})
        except Exception as e:
            db.session.rollback()
            print(f"Error saving petition data: {str(e)}")
            return jsonify({'success': False, 'message': f'Error saving petition data: {str(e)}'}), 500
    
    # Handle GET request to retrieve existing petition data
    elif request.method == 'GET':
        print("Processing GET request to retrieve petition data")
        
        # Try to find petition any way possible
        existing_petition = None
        search_methods = []
        
        # 1. Try by user_id
        if user_id:
            search_methods.append(f"user_id={user_id}")
            existing_petition = Petition.query.filter_by(user_id=user_id).order_by(Petition.created_at.desc()).first()
            if existing_petition:
                print(f"Found petition by user_id: {existing_petition.id}")
        
        # 2. Try by email in session
        if not existing_petition and user_email:
            search_methods.append(f"email={user_email}")
            existing_petition = Petition.query.filter_by(email=user_email).order_by(Petition.created_at.desc()).first()
            if existing_petition:
                print(f"Found petition by email in session: {existing_petition.id}")
                
                # Link this petition to the user if they're logged in
                if user_id and existing_petition.user_id != user_id:
                    print(f"Linking petition {existing_petition.id} to user_id {user_id}")
                    existing_petition.user_id = user_id
                    db.session.commit()
        
        # 3. Last resort - get all petitions and look for a match
        if not existing_petition and (user_id or user_email):
            print("Trying to find ANY petition in the database for this user...")
            all_petitions = Petition.query.all()
            print(f"Found {len(all_petitions)} total petitions in database")
            
            if user_id:
                print(f"Looking for any petition with user_id={user_id}")
                for p in all_petitions:
                    if p.user_id == user_id:
                        existing_petition = p
                        print(f"Found petition by user_id search: {existing_petition.id}")
                        break
            
            if not existing_petition and user_email:
                print(f"Looking for any petition with email={user_email}")
                for p in all_petitions:
                    if p.email == user_email:
                        existing_petition = p
                        print(f"Found petition by email search: {existing_petition.id}")
                        # Link to user_id if needed
                        if user_id and existing_petition.user_id != user_id:
                            existing_petition.user_id = user_id
                            db.session.commit()
                            print(f"Linked petition {existing_petition.id} to user_id {user_id}")
                        break
        
        if existing_petition:
            print(f"Returning petition data for ID: {existing_petition.id}")
            # Convert dates to string format for JSON serialization
            petition_data = {}
            for column in existing_petition.__table__.columns:
                value = getattr(existing_petition, column.name)
                
                # Handle date objects
                if isinstance(value, (datetime, date)):
                    petition_data[column.name] = value.isoformat()
                else:
                    petition_data[column.name] = value
            
            return jsonify({'success': True, 'petition': petition_data})
        else:
            search_methods_str = ', '.join(search_methods)
            print(f"NO PETITION FOUND despite searching by: {search_methods_str}")
            return jsonify({'success': False, 'message': f'No petition found for user after trying: {search_methods_str}'}), 404

    # Handle GET request to retrieve existing petition data
    elif request.method == 'GET':
        print("Processing GET request to fetch petition data")
        
        # Try different strategies to find the user's petition
        search_methods = []
        existing_petition = None
        
        # 1. Try by user_id
        if user_id:
            search_methods.append(f"user_id={user_id}")
            existing_petition = Petition.query.filter_by(user_id=user_id).order_by(Petition.created_at.desc()).first()
            if existing_petition:
                print(f"Found petition by user_id: {existing_petition.id}")
        
        # 2. Try by email in session
        if not existing_petition and user_email:
            search_methods.append(f"email={user_email}")
            existing_petition = Petition.query.filter_by(email=user_email).order_by(Petition.created_at.desc()).first()
            if existing_petition:
                print(f"Found petition by email in session: {existing_petition.id}")
                
                # Link this petition to the user if they're logged in
                if user_id and existing_petition.user_id != user_id:
                    print(f"Linking petition {existing_petition.id} to user_id {user_id}")
                    existing_petition.user_id = user_id
                    db.session.commit()
        
        # 3. Last resort - get all petitions and look for a match
        if not existing_petition and (user_id or user_email):
            print("Trying to find ANY petition in the database for this user...")
            all_petitions = Petition.query.all()
            print(f"Found {len(all_petitions)} total petitions in database")
            
            if user_id:
                print(f"Looking for any petition with user_id={user_id}")
                for p in all_petitions:
                    if p.user_id == user_id:
                        existing_petition = p
                        print(f"Found petition by user_id search: {existing_petition.id}")
                        break
            
            if not existing_petition and user_email:
                print(f"Looking for any petition with email={user_email}")
                for p in all_petitions:
                    if p.email == user_email:
                        existing_petition = p
                        print(f"Found petition by email search: {existing_petition.id}")
                        # Link to user_id if needed
                        if user_id and existing_petition.user_id != user_id:
                            existing_petition.user_id = user_id
                            db.session.commit()
                            print(f"Linked petition {existing_petition.id} to user_id {user_id}")
                        break
        
        if existing_petition:
            print(f"Returning petition data for ID: {existing_petition.id}")
            # Convert dates to string format for JSON serialization
            petition_data = {}
            for column in existing_petition.__table__.columns:
                value = getattr(existing_petition, column.name)
                
                # Handle date objects
                if isinstance(value, (datetime, date)):
                    petition_data[column.name] = value.isoformat()
                else:
                    petition_data[column.name] = value
            
            return jsonify({'success': True, 'petition': petition_data})
        else:
            search_methods_str = ', '.join(search_methods)
            print(f"NO PETITION FOUND despite searching by: {search_methods_str}")
            return jsonify({'success': False, 'message': f'No petition found for user after trying: {search_methods_str}'}), 404
    
    # If request is neither POST nor GET
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405


@app.route('/attorney/documents/validate_passport', methods=['POST'])
@login_required
def validate_passport():
    file = request.files.get('file')
    doc_type = request.form.get('document_type')

    if not file or doc_type != 'passport':
        return jsonify({'verified': False, 'message': 'Invalid input.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'verified': False, 'message': 'Unsupported file type.','reason':'upload a pdf file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Step 1: Image similarity check
        indian_passport_similarity = compare_passport_pdf_to_reference(pdf_path=filepath, ref_path=passport_ref_file_path)
        if not indian_passport_similarity>=0.80:
            return jsonify({'verified': False, 'message': 'Image similarity check failed.','reason':'Attached file is not passport.Please attach passport.'}), 400

        # Step 2: OCR + Text check
        text = extract_text_from_file(filepath)
        print("text", text)
        if not text or len(text.strip()) < 20:
            return jsonify({'verified': False, 'message': 'No readable text detected.','reason':'Unable to extract text due to poor quality of image'}), 400

        lower = text.lower()
        if "republic of india" not in lower or not ("passport no" in lower or "p<ind" in lower):
            return jsonify({'verified': False, 'message': 'Not a standard Indian passport.'}), 400

        # Step 3: Extract and validate passport fields
        data = extract_passport_data(text)

        # valid = all(data.get(field) for field in ["passport_number", "date_of_issue", "date_of_expiry"])

        required = ['passport_number','date_of_issue','date_of_expiry']
        # required = ["passportNumber", "date_of_issue", "date_of_expiry"]
        missing = [f for f in required if not str(data.get(f, "")).strip()]
        print(data)
        print(type(data))
        key_map = {
            "passport_number": "passportNumber",
            "date_of_expiry": "dateOfExpiry",
        }
        data = rename_keys_in_place(data, key_map)
        print(data)
        if missing:
            return jsonify({'verified': False, 'message': f'Missing fields: {", ".join(missing)}'}), 400

        return jsonify({'verified': True, 'message': 'Passport is verified.','passport_data':data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'verified': False, 'message': 'Internal server error.', 'error': str(e)}), 500


@app.route('/attorney/documents/validate_education', methods=['POST'])
@login_required
def validate_education():
    file = request.files.get('file')
    doc_type = request.form.get('document_type')

    if not file or doc_type != 'education':
        return jsonify({'verified': False, 'message': 'Invalid input.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'verified': False, 'message': 'Unsupported file type.','reason':'upload pdf file.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        text = extract_text_from_certificate(filepath)        

        if not text or len(text.strip()) < 20:
            return jsonify({'verified': False, 'message': 'No readable text detected.','reason':'Uploaded file is of poor quality'}), 400

        text_lower = text.lower()

        keywords = ["certificate","college","bachelor","master","awarded","dean","completion","university"]

        # Check if any of the keywords are present in the text
        is_keyword_found = any(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) for keyword in keywords)

        if is_keyword_found and len(text)>400:
            return jsonify({'verified': False, 'message': 'Resume might be uploadedm, Certificate is not uploaded','reason':'Resume might be uploadedm, Certificate is not uploaded'}), 400
        elif not is_keyword_found:
            return jsonify({'verified': False, 'message': 'Certificate is not uploaded','reason':'Certificate is not uploaded'}), 400

        prompt =  f"""You are a question answering bot. Based on the context and questions provided, generate appropriate answers in JSON format.\n\n
        
        context: {text}
        give following output

        Questions:
        1. Which university did the user complete their education at?
        2. What is the education mentioned in the certificate?
        3. Who has received the certificate
        4. education completion date"""

        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=100)

        split_data = re.split(r'\d+\.\s*', tokenizer.decode(outputs[0], skip_special_tokens=True))

        # Clean up the data to remove any empty strings from the split
        split_data = [item.strip() for item in split_data if item.strip()]

        # Assign each part to the correct category
        result_dict = {
            'university': split_data[0],'education': split_data[1],'name': split_data[2],'date': split_data[3]
        }
        print(result_dict)

        if not result_dict:
            return jsonify({'verified': False, 'message': f'Missing fields: {", ".join(result_dict)}'}), 400

        return jsonify({'verified': True, 'message': 'Education document is verified.', 'edu_dict':result_dict})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'verified': False, 'message': 'Internal server error.', 'error': str(e)}), 500


@app.route('/attorney/documents/validate_emp_support_doc', methods=['POST'])
@login_required
def validate_emp_doc():
    file = request.files.get('file')
    doc_type = request.form.get('document_type')

    if not file or doc_type != 'emp_support':
        return jsonify({'verified': False, 'message': 'Invalid input.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'verified': False, 'message': 'Unsupported file type.','reason':'Upload pdf file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    text = extract_text_from_file(filepath)
    ref_word_path = employer_ref_file_path
    
    ref_emp_text = extract_text_from_word(ref_word_path)
    embedding_doc = model_emp.encode([text])
    embedding_ref = model_emp.encode([ref_emp_text])
    similarity_score = cosine_similarity(embedding_doc, embedding_ref)
    print("similarity score of emplye support doc", similarity_score)

    if not similarity_score[0][0] > 0.8:
        return jsonify({'verified': False, 'message': 'Employee Support Document is not uploaded','reason':'Please upload Employee support document'}), 400

    data = {
        "employee_name": extract(r"Employee Name:\s*(.+)", text=text),
        "organization_name": extract(r"Organization name:\s*(.+)", text=text),
        "position": extract(r"Position:\s*(.+)", text=text),
        "fein_number": extract(r"\b(\d{9})\b", text=text),
        "lca_number": extract(r"\b(I-\d{4}-\d{5}-\d{5})\b", text=text)
    }
    valid = all(data.values())

    return jsonify({
        "verified": valid,
        "message": "Employer letter verified and processed successfully." if valid else "Missing required employer letter fields.",
        "eligibility": "Eligible" if valid else "Ineligible",
        "extracted_emp_doc_data": data
    })


@app.route("/attorney/documents/validate_cv", methods=["POST"])
@login_required
def validate_cv():
    file = request.files.get('file')
    doc_type = request.form.get('document_type')

    if not file or doc_type != 'resume':
        return jsonify({'verified': False, 'message': 'Invalid input.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'verified': False, 'message': 'Unsupported file type.'}), 400

    file = request.files.get("file")
    if not file:
        return jsonify({"verified": False, "message": "No file provided."}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    text = extract_text_from_file(filepath)
    if not text or len(text.strip()) < 20:
            return jsonify({'verified': False, 'message': 'No readable text detected.','reason':'Unable to extract text due to poor quality of image'}), 400

    text_lower = text.lower()

    keywords = ["certificate","about","me","skills","email","education","experience","project","university"]

    # Check if any of the keywords are present in the text
    is_keyword_found = any(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) for keyword in keywords)

    if is_keyword_found and len(text)<100:
        return jsonify({'verified': False, 'message': 'Resume is not uploaded, Certificate might be uploaded','reason':'Resume is not uploaded, Certificate might be uploaded'}), 400
    elif not is_keyword_found:
        return jsonify({'verified': False, 'message': 'Resume is not uploaded'}), 400
    
    features = extract_cv_features(text)
    print(features)

    section_count = sum(features['sections_found'].values())

    if (section_count >= 3 and features['email'] is not None and features['phone'] is not None and
        features['date_range'] is not None and features['coding_languages'] and 100 <= features['word_count'] <= 200
    ):
        valid = True
    else:
        valid = False

    messages = []
    if section_count < 3: messages.append("At least 3 sections required.")
    if not features['email']: messages.append("Missing valid email.")
    if not features['phone']: messages.append("Missing valid phone number.")
    if not features['date_range']: messages.append("Missing work experience date range.")
    if not features['coding_languages']: messages.append("Missing coding language.")
    if features['word_count'] < 100: messages.append("CV too short.")
    elif features['word_count'] > 200: messages.append("CV too long.")    

    return jsonify({
        "verified": valid,
        "message": "CV validation successful." if valid else " ".join(messages),
        "eligibility": "Eligible" if valid else "Ineligible",
        "extracted_resume_data": features})


@app.route('/process-documents', methods=['POST'])
@login_required
def process_documents():
    data = request.get_json()
    print("data from docs",data)
    passport = data.get('passportNumber').strip()
    passport_expiry_date = data.get('dateOfExpiry').strip()
    passport_expiry_date = datetime.strptime(passport_expiry_date, '%d/%m/%Y').date()
    full_name_emp = data.get('employee_name').strip()
    full_name_edu = data.get('name').strip()
    
    fein_number = str(data.get("fein_number"))
    if fein_number:
        fein_number = fein_number.strip()
    lca_number = data.get("lca_number").strip()
    education = data.get("education").strip()

    if not passport or not full_name_emp or not fein_number or not lca_number or not full_name_edu:
        return jsonify({'error': 'Missing required fields'}), 400

    # Split full_name_emp
    name_parts = full_name_emp.split()
    name_parts_ed = full_name_edu.split()
    if len(name_parts) < 2:
        return jsonify({'error': 'Full name must include at least first and last name'}), 400
    
    first_name, first_name_ed = name_parts[0], name_parts_ed[0]
    middle_name, middle_name_ed = name_parts[1] if len(name_parts) > 2 else '', name_parts_ed[1] if len(name_parts_ed)>2 else''
    last_name ,last_name_ed = name_parts[-1], name_parts_ed[-1]

    # Connect to MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='123Qwerty!@#',
        database='Immigraassist'
    )
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT * FROM petitions
    WHERE passport_number = %s
        AND beneficiary_given_name = %s
        AND beneficiary_middle_name = %s
        AND beneficiary_family_name = %s
        AND fein =%s
        AND lca_number = %s
        AND passport_expiry_date = %s
    ORDER BY created_at DESC
    LIMIT 1
    """

    params = (
        passport,
        first_name,
        middle_name,
        last_name,
        fein_number, 
        lca_number,
        passport_expiry_date
    )
    cursor.execute(query, params)
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    if not records:
        return jsonify({'message': 'Form data and document data are not matching',"verified":False}), 404

    print(records)

    # Match and mismatch tracking
    response_records = []
    for record in records:
        matches, mismatches = compare("fein_number", fein_number, record.get('fein'))
        matches, mismatches = compare("education", education, record.get('education_qualification'))
        matches, mismatches = compare("lca_number", lca_number, record.get('lca_number'))
        matches, mismatches = compare("passport_expiry_data", passport_expiry_date, record.get('passport_expiry_date'))

        response_records.append({
            'record_id': record.get('id'),  # adjust to your PK field
            'matches': matches,
            'mismatches': mismatches
        })
    if mismatches:
        return jsonify({'message':'Mismatched are found',
                        "mismatching_fields":response_records,
                        "verified":False})

    return jsonify({
        'message': 'All records from form and documents are correct',
        "verified":True,
        "mismatching_fields":response_records
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create Admin user if it doesn't exist
        Admin_user = User.query.filter_by(email='Admin@example.com').first()
        if not Admin_user:
            Admin = User(
                firstname='Admin',
                lastname='User',
                email='Admin@example.com',
                phone='1234567890',
                password=generate_password_hash('Admin123'),
                role='Admin'
            )
            db.session.add(Admin)
            db.session.commit()
            
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin = User(
                firstname='Jane',
                lastname='Admin',
                email='admin@example.com',
                phone='9876543210',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            
    app.run(debug=True)