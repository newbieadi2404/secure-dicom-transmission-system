from .db import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="success")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def log_event(user_email, action, details=None, status="success"):
    try:
        new_log = AuditLog(
            user_email=user_email,
            action=action,
            details=details,
            status=status
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log audit event: {e}")
