from .db import db
from datetime import datetime

class Record(db.Model):
    __tablename__ = "records"

    id = db.Column(db.Integer, primary_key=True)
    patient_email = db.Column(db.String(120), nullable=False)
    doctor_email = db.Column(db.String(120), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(300))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Healthcare metadata
    modality = db.Column(db.String(50), default="DICOM")
    body_part = db.Column(db.String(100), nullable=True)
    clinical_notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default="NORMAL") # NORMAL, URGENT, EMERGENCY
