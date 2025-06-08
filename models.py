from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')

    petitions = db.relationship('Petition', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


class Petition(db.Model):
    __tablename__ = 'petitions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Part 1: Petitioner Information
    petitioner_family_name = db.Column(db.String(80), nullable=False)
    petitioner_given_name = db.Column(db.String(80), nullable=False)
    petitioner_middle_name = db.Column(db.String(80))
    company_name = db.Column(db.String(255), nullable=False)
    in_care_of = db.Column(db.String(255))
    street_address = db.Column(db.String(255), nullable=False)
    apt_ste_flr = db.Column(db.String(50))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), nullable=False)
    daytime_phone = db.Column(db.String(20), nullable=False)
    mobile_phone = db.Column(db.String(20))
    email = db.Column(db.String(120), nullable=False)
    fein = db.Column(db.String(20), nullable=False)
    
    # Part 2: Basis for Classification
    basis_for_classification = db.Column(db.String(50), nullable=False)
    
    # Part 3: Beneficiary Information
    beneficiary_family_name = db.Column(db.String(80), nullable=False)
    beneficiary_given_name = db.Column(db.String(80), nullable=False)
    beneficiary_middle_name = db.Column(db.String(80))
    other_family_name = db.Column(db.String(80))
    other_given_name = db.Column(db.String(80))
    other_middle_name = db.Column(db.String(80))
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    ssn = db.Column(db.String(20))
    alien_number = db.Column(db.String(20))
    country_of_birth = db.Column(db.String(100), nullable=False)
    country_of_citizenship = db.Column(db.String(100), nullable=False)
    passport_number = db.Column(db.String(50), nullable=False)
    # passport_number = db.Column(db.String(50), nullable=False, unique=True)
    passport_expiry_date = db.Column(db.Date, nullable=False)
    education_qualification = db.Column(db.String(255), nullable=False)
    
    # Part 4: Processing Information
    foreign_street = db.Column(db.String(255), nullable=False)
    foreign_apt = db.Column(db.String(50))
    foreign_city = db.Column(db.String(100), nullable=False)
    foreign_state = db.Column(db.String(100))
    foreign_postal = db.Column(db.String(20))
    foreign_country = db.Column(db.String(100), nullable=False)
    valid_passport = db.Column(db.String(5), nullable=False)
    passport_explanation = db.Column(db.Text)
    
    # Part 5: Basic Information About Proposed Employment
    job_title = db.Column(db.String(255), nullable=False)
    lca_number = db.Column(db.String(100), nullable=False)
    work_street_1 = db.Column(db.String(255))
    work_apt_1 = db.Column(db.String(50))
    work_city_1 = db.Column(db.String(100))
    work_state_1 = db.Column(db.String(50))
    work_zip_1 = db.Column(db.String(20))
    third_party_1 = db.Column(db.String(5))
    third_party_org_1 = db.Column(db.String(255))
    itinerary = db.Column(db.String(5))
    work_offsite = db.Column(db.String(5))
    full_time = db.Column(db.String(5))
    hours_per_week = db.Column(db.Integer)
    wage_amount = db.Column(db.Float, nullable=False)
    wage_period = db.Column(db.String(20), nullable=False)
    
    # Status tracking
    state = db.Column(db.String(50), default='Pending')
    
    # Additional fields for attorney review
    form_data = db.Column(db.Text)  # JSON string containing form data
    feedback = db.Column(db.Text)   # JSON string containing feedback history
    admin_notes = db.Column(db.Text)  # Notes from attorney/admin
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Petition {self.id} by User {self.user_id}>'
