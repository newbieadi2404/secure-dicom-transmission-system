import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
import os

from backend.models.db import db, init_db
from backend.routes.doctor import doctor_bp
from backend.routes.patient import patient_bp
from backend.routes.auth import auth_bp
from backend.routes.admin import admin_bp
from backend.utils.errors import register_error_handlers
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Determine the absolute path for the database file
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-insecure-change-me')

# SMTP Configuration
app.config['SMTP_EMAIL'] = os.environ.get('SMTP_EMAIL', 'chintu01032005@gmail.com')
app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')

db.init_app(app)
jwt = JWTManager(app)
swagger = Swagger(app)

# Register Error Handlers
register_error_handlers(app)

app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
app.register_blueprint(doctor_bp, url_prefix="/api/v1/doctor")
app.register_blueprint(patient_bp, url_prefix="/api/v1/patient")
app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")

@app.cli.command()
def initdb():
    init_db(app)
    print("Database initialized!")

@app.route("/")
def home():
    return {"message": "Backend running"}

if __name__ == "__main__":
    init_db(app)
    app.run(debug=True, port=5000)

