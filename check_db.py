from app import app, db, Petition, User
from flask import Flask

with app.app_context():
    # Count total petitions
    total_petitions = Petition.query.count()
    print(f'Total petitions in DB: {total_petitions}')
    
    # Get all users
    users = User.query.all()
    print(f'Total users in DB: {len(users)}')
    
    # Check petitions by user
    print('\nPetitions by user:')
    for user in users:
        user_petitions = Petition.query.filter_by(user_id=user.id).all()
        print(f'User {user.id} ({user.email}): {len(user_petitions)} petitions')
        
        # Print petition details
        if user_petitions:
            print('  Petition IDs:', [p.id for p in user_petitions])
            
    # Check if there are any petitions without user_id
    unassigned = Petition.query.filter_by(user_id=None).all()
    print(f'\nUnassigned petitions: {len(unassigned)}')
    if unassigned:
        print('  Petition IDs:', [p.id for p in unassigned])
