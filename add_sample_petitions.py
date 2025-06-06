from app import app, db, Petition, User
from datetime import datetime, timedelta
import random

with app.app_context():
    # Get the current user ID from the session
    # Since we can't access the session directly, we'll add petitions to user ID 1
    # which appears to be the admin user you're currently logged in as
    user_id = 1
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        print(f"User with ID {user_id} not found")
        exit(1)
    
    print(f"Adding sample petitions for user: {user.email}")
    
    # Sample form types
    form_types = ['I-129 Petition', 'I-140 Petition', 'I-485 Application', 'I-765 Application']
    
    # Sample statuses
    statuses = ['Under Review', 'Approved', 'Pending Documents', 'Rejected', 'Needs Attention']
    
    # Create 3 additional sample petitions
    for i in range(3):
        # Create dates within the last 30 days
        submission_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        # Create a new petition
        new_petition = Petition(
            user_id=user_id,
            email=user.email,
            form_type=random.choice(form_types),
            status=random.choice(statuses),
            submission_date=submission_date,
            first_name=user.firstname,
            last_name=user.lastname
        )
        
        db.session.add(new_petition)
        print(f"Added petition: {new_petition.form_type} with status {new_petition.status}")
    
    # Commit the changes
    db.session.commit()
    print("Sample petitions added successfully!")
    
    # Verify the petitions were added
    user_petitions = Petition.query.filter_by(user_id=user_id).all()
    print(f"User now has {len(user_petitions)} petitions")
    print("Petition IDs:", [p.id for p in user_petitions])
