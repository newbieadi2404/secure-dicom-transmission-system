from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

db = SQLAlchemy()

UPLOADS_DIR = Path('uploads')
UPLOADS_DIR.mkdir(exist_ok=True)

def init_db(app):
    with app.app_context():
        from backend.models.user import User  # noqa: F401
        from backend.models.record import Record  # noqa: F401
        from backend.models.audit import AuditLog  # noqa: F401
        db.create_all()
        print('✅ Database tables created')

