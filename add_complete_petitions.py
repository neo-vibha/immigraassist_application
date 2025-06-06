from app import app, db, Petition, User
from datetime import datetime, timedelta, date
import random

with app.app_context():
    # Get the current user ID from the session
    # Since we can't access the session directly, we'll add petitions to user ID 1
    # which appears to be the admin user you're currently logged in as
    user_id = 1
    
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        print(f"User with ID {user_id} not found")
        exit(1)
    
    print(f"Adding sample petitions for user: {user.email}")
    
    # Sample statuses
    statuses = ['Under Review', 'Approved', 'Pending Documents', 'Rejected']
    
    # Create 3 additional sample petitions
    for i in range(3):
        # Create dates within the last 30 days
        submission_date = datetime.now() - timedelta(days=random.randint(1, 30))
        birth_date = date(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28))
        passport_expiry = date.today() + timedelta(days=365 * random.randint(1, 5))
        
        # Create a new petition with all required fields
        petition_status = random.choice(statuses)
        new_petition = Petition(
            user_id=user_id,
            petitioner_family_name=user.lastname,
            petitioner_given_name=user.firstname,
            petitioner_middle_name="",
            company_name=f"Company {i+1}",
            in_care_of="",
            street_address=f"{random.randint(100, 999)} Main St",
            apt_ste_flr="",
            city="New York",
            state="NY",  # This is the US state field
            zip_code=f"1000{i}",
            province="",
            postal_code="",
            country="United States",
            daytime_phone="123-456-7890",
            mobile_phone="",
            email=user.email,
            fein=f"12-345678{i}",
            basis_for_classification="H-1B",
            beneficiary_family_name=f"Beneficiary{i}",
            beneficiary_given_name=f"Name{i}",
            beneficiary_middle_name="",
            other_family_name="",
            other_given_name="",
            other_middle_name="",
            birth_date=birth_date,
            gender="Male" if i % 2 == 0 else "Female",
            ssn="",
            alien_number="",
            country_of_birth="India",
            country_of_citizenship="India",
            passport_number=f"P{random.randint(10000000, 99999999)}",
            passport_expiry_date=passport_expiry,
            education_qualification="Bachelor's Degree",
            foreign_street=f"{random.randint(100, 999)} Foreign St",
            foreign_apt="",
            foreign_city="Mumbai",
            foreign_state="Maharashtra",
            foreign_postal="400001",
            foreign_country="India",
            valid_passport="Yes",
            passport_explanation="",
            job_title=f"Software Engineer Level {i+1}",
            lca_number=f"LCA-{random.randint(10000, 99999)}",
            work_street_1=f"{random.randint(100, 999)} Work St",
            work_apt_1="",
            work_city_1="San Francisco",
            work_state_1="CA",
            work_zip_1="94105",
            third_party_1="No",
            third_party_org_1="",
            itinerary="No",
            work_offsite="No",
            full_time="Yes",
            hours_per_week=40,
            wage_amount=100000 + (i * 10000),
            wage_period="Year",
            created_at=submission_date
        )
        
        # Set the petition status after creation to avoid the naming conflict
        new_petition.state = petition_status
        
        db.session.add(new_petition)
        print(f"Added petition with status {new_petition.state}")
    
    # Commit the changes
    db.session.commit()
    print("Sample petitions added successfully!")
    
    # Verify the petitions were added
    user_petitions = Petition.query.filter_by(user_id=user_id).all()
    print(f"User now has {len(user_petitions)} petitions")
    print("Petition IDs:", [p.id for p in user_petitions])
