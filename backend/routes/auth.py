from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from backend.utils.validation import validate_request
from backend.utils.schemas import UserRegisterSchema, UserLoginSchema

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/register', methods=['POST'])
@validate_request(UserRegisterSchema)
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: UserRegister
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: doctor@test.com
            password:
              type: string
              example: password123
            role:
              type: string
              enum: [PATIENT, DOCTOR, ADMIN]
              default: PATIENT
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid request body
      409:
        description: User already exists
    """
    from backend.models.db import db
    from backend.models.user import User
    from backend.models.audit import log_event
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'PATIENT')

    if role not in ['PATIENT', 'DOCTOR', 'ADMIN']:
        return jsonify({'error': 'Invalid role'}), 400

    if User.query.filter_by(email=email).first():
        log_event(email, 'REGISTER_FAILED', 'User already exists', 'error')
        return jsonify({'error': 'User exists'}), 409

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()

    log_event(email, 'REGISTER', f'New {role} account established')

    return jsonify({
        'message': 'User created',
        'user_id': user.id,
        'role': user.role
    }), 201

@auth_bp.route('/login', methods=['POST'])
@validate_request(UserLoginSchema)
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: UserLogin
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: doctor@test.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    from backend.models.db import db
    from backend.models.user import User
    from backend.models.audit import log_event
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        log_event(email or 'unknown', 'LOGIN_FAILED', 'Invalid credentials', 'error')
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(
        identity={'email': email, 'role': user.role},
        expires_delta=timedelta(seconds=86400)  # 24h
    )

    log_event(email, 'LOGIN', 'Secure authorization successful')

    return jsonify({
        'token': token,
        'role': user.role,
        'email': email
    })

# Protected test endpoint
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    identity = get_jwt_identity()
    return jsonify({'identity': identity})

