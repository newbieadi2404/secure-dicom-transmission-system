import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app, db
from backend.models.user import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all() # Ensure tables are created in the correct DB
    # Check if doctor exists
    if not User.query.filter_by(email='doctor@test.com').first():
        doctor = User(
            email='doctor@test.com',
            password_hash=generate_password_hash('pass'),
            role='DOCTOR'
        )
        db.session.add(doctor)
        print("Created doctor@test.com")
    
    # Check if patient exists
    if not User.query.filter_by(email='patient@test.com').first():
        patient = User(
            email='patient@test.com',
            password_hash=generate_password_hash('pass'),
            role='PATIENT'
        )
        db.session.add(patient)
        print("Created patient@test.com")
    
    # Check if admin exists
    if not User.query.filter_by(email='admin@test.com').first():
        admin = User(
            email='admin@test.com',
            password_hash=generate_password_hash('pass'),
            role='ADMIN'
        )
        db.session.add(admin)
        print("Created admin@test.com")
    
    db.session.commit()

    print("Database seeding complete!")
