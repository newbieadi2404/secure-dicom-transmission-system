from .db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # DOCTOR / PATIENT / ADMIN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Healthcare-specific fields
    full_name = db.Column(db.String(120), nullable=True)
    specialty = db.Column(db.String(120), nullable=True) # For doctors
    license_number = db.Column(db.String(50), nullable=True) # For doctors
    date_of_birth = db.Column(db.String(20), nullable=True) # For patients
    blood_group = db.Column(db.String(10), nullable=True) # For patients


    def __repr__(self):
        return f"<User {self.email}>"