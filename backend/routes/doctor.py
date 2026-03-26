from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import tempfile
import os
import logging
import json

doctor_bp = Blueprint("doctor", __name__)

@doctor_bp.route("/send", methods=["POST"])
@jwt_required()
def send_file():
    from backend.models.db import db
    from backend.models.user import User
    from backend.models.record import Record
    from backend.models.audit import log_event
    from services.encryption_service import process_and_send
    try:
        # AUTH VALIDATION
        identity = get_jwt_identity()

        if not identity or identity.get("role") != "DOCTOR":
            return jsonify({"error": "Doctor only"}), 403

        doctor_email = identity.get("email")
        logging.info(f"DEBUG: doctor_email={doctor_email}, role={identity.get('role')}")

        # Verify doctor exists in DB
        doctor = User.query.filter_by(email=doctor_email, role="DOCTOR").first()
        if not doctor:
            logging.error(f"DEBUG: Doctor not found in DB: email={doctor_email}")
            log_event(doctor_email, 'SEND_FAILED', 'Unknown sender', 'error')
            return jsonify({"error": "Unknown sender"}), 404

        # INPUT VALIDATION
        if "file" not in request.files:
            return jsonify({"error": "DICOM file required"}), 400

        dicom_file = request.files["file"]

        if not dicom_file.filename:
            return jsonify({"error": "Empty filename"}), 400

        recipient_email = request.form.get("patient_email")
        body_part = request.form.get("body_part", "UNSPECIFIED")
        priority = request.form.get("priority", "NORMAL")
        clinical_notes = request.form.get("clinical_notes", "")

        if not recipient_email or "@" not in recipient_email:
            return jsonify({"error": "Valid recipient email required"}), 400

        # Verify recipient exists (can be PATIENT or DOCTOR)
        recipient = User.query.filter_by(email=recipient_email).first()
        if not recipient:
            log_event(doctor_email, 'SEND_FAILED', f'Recipient {recipient_email} not registered', 'error')
            return jsonify({"error": "Recipient not registered"}), 404

        filename = secure_filename(dicom_file.filename)

        # TEMP FILE SAVE
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as temp_file:
            dicom_file.save(temp_file.name)
            temp_path = temp_file.name

        # ENCRYPT + STORE
        # Automatically generate certificate for the doctor if needed
        from services.certificate_service import generate_user_certificate
        from services.key_service import resolve_public_key
        
        doctor_public = resolve_public_key(doctor_email)
        if doctor_public:
            # We generate and return the certificate string to be used in the process_and_send
            cert_dict = generate_user_certificate(doctor_email, doctor_public)
            doctor_cert = json.dumps(cert_dict)
        else:
            doctor_cert = None

        result = process_and_send(
            temp_path,
            doctor_email,
            recipient_email,
            certificate=doctor_cert
        )

        smt_path = result.get("file")

        if not smt_path:
            raise Exception("Encryption failed: no output file")

        # DB RECORD
        record = Record(
            patient_email=recipient_email, # We use patient_email for the recipient
            doctor_email=doctor_email,      # We use doctor_email for the sender
            filename=filename,
            file_path=str(smt_path),
            status="pending",
            body_part=body_part,
            priority=priority,
            clinical_notes=clinical_notes
        )

        db.session.add(record)
        db.session.commit()

        log_event(doctor_email, 'SEND_RECORD', f'Encrypted record sent to {recipient_email}: {filename}')
        logging.info(f"[SEND] {doctor_email} → {recipient_email}: {filename}")

        return jsonify({
            "success": True,
            "record_id": record.id,
            "file_path": smt_path,
            "message": "DICOM encrypted and stored"
        }), 201

    except Exception as e:
        logging.error(f"[ERROR] Send failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # cleanup temp file
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass

@doctor_bp.route("/records", methods=["GET"])
@jwt_required()
def get_records():
    from backend.models.record import Record
    identity = get_jwt_identity()
    if identity['role'] != 'DOCTOR':
        return jsonify({'error': 'Doctor only'}), 403

    doctor_email = identity['email']
    # Sent by this doctor
    records = Record.query.filter_by(doctor_email=doctor_email).order_by(Record.created_at.desc()).all()

    return jsonify([{
        'id': r.id,
        'patient_email': r.patient_email,
        'filename': r.filename,
        'status': r.status,
        'created_at': r.created_at.isoformat(),
        'body_part': r.body_part,
        'priority': r.priority
    } for r in records])

@doctor_bp.route("/inbox", methods=["GET"])
@jwt_required()
def get_inbox():
    from backend.models.record import Record
    identity = get_jwt_identity()
    if identity['role'] != 'DOCTOR':
        return jsonify({'error': 'Doctor only'}), 403

    doctor_email = identity['email']
    # Sent TO this doctor
    records = Record.query.filter_by(patient_email=doctor_email).order_by(Record.created_at.desc()).all()

    return jsonify([{
        'id': r.id,
        'sender': r.doctor_email or 'System',
        'filename': r.filename,
        'status': r.status,
        'created_at': r.created_at.isoformat(),
        'body_part': r.body_part,
        'priority': r.priority
    } for r in records])

@doctor_bp.route("/decrypt/<int:record_id>", methods=["POST"])
@jwt_required()
def decrypt_file_route(record_id):
    from backend.models.db import db
    from backend.models.record import Record
    from backend.models.audit import log_event
    from pathlib import Path
    from config import BASE_DIR, UPLOADS_DIR
    
    identity = get_jwt_identity()
    if identity['role'] != 'DOCTOR':
        return jsonify({'error': 'Doctor only'}), 403

    doctor_email = identity['email']
    record = Record.query.filter_by(id=record_id, patient_email=doctor_email).first()
    if not record:
        log_event(doctor_email, 'DECRYPT_FAILED', f'Record {record_id} not found', 'error')
        return jsonify({'error': 'Record not found'}), 404

    if record.status == 'decrypted':
        return jsonify({'error': 'Already decrypted'}), 400

    try:
        from services.decryption_service import decrypt_file
        
        file_path = Path(record.file_path)
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

        result = decrypt_file(file_path)
        output_path = Path(result['output'])

        decrypted_dir = UPLOADS_DIR / 'decrypted'
        decrypted_dir.mkdir(parents=True, exist_ok=True)
        decrypted_npy = decrypted_dir / f"record_dr_{record_id}.npy"
        output_path.replace(decrypted_npy)

        record.status = 'decrypted'
        record.file_path = str(decrypted_npy)
        db.session.commit()

        log_event(doctor_email, 'DECRYPT_RECORD', f'Doctor decrypted imaging record: {record.filename}')

        return jsonify({
            'success': True,
            'output_path': str(decrypted_npy),
            'message': 'Decrypted successfully'
        })

    except Exception as e:
        logging.error(f"Doctor decrypt failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@doctor_bp.route("/patients", methods=["GET"])
@jwt_required()
def get_patients():
    from backend.models.record import Record
    from backend.models.user import User
    identity = get_jwt_identity()
    if identity['role'] != 'DOCTOR':
        return jsonify({'error': 'Doctor only'}), 403

    doctor_email = identity['email']
    
    # Get distinct emails this doctor has interacted with (sent to or received from)
    from backend.models.db import db
    from sqlalchemy import or_
    
    # Sent to
    sent_to = db.session.query(Record.patient_email.label('email')).filter_by(doctor_email=doctor_email)
    # Received from
    received_from = db.session.query(Record.doctor_email.label('email')).filter_by(patient_email=doctor_email)
    
    distinct_emails = sent_to.union(received_from).distinct().all()
    
    interacted_list = []
    for (email,) in distinct_emails:
        # Find latest interaction
        last_sent = Record.query.filter_by(doctor_email=doctor_email, patient_email=email).order_by(Record.created_at.desc()).first()
        last_received = Record.query.filter_by(doctor_email=email, patient_email=doctor_email).order_by(Record.created_at.desc()).first()
        
        last_interaction = None
        if last_sent and last_received:
            last_interaction = last_sent if last_sent.created_at > last_received.created_at else last_received
        else:
            last_interaction = last_sent or last_received
            
        total_count = Record.query.filter(or_(
            db.and_(Record.doctor_email == doctor_email, Record.patient_email == email),
            db.and_(Record.doctor_email == email, Record.patient_email == doctor_email)
        )).count()
        
        interacted_list.append({
            "email": email,
            "last_interaction": last_interaction.created_at.isoformat() if last_interaction else None,
            "total_records": total_count,
            "status": "verified"
        })
    
    return jsonify(interacted_list)

@doctor_bp.route("/record/<int:record_id>", methods=["DELETE"])
@jwt_required()
def revoke_record(record_id):
    from backend.models.db import db
    from backend.models.record import Record
    from backend.models.audit import log_event
    import os
    
    identity = get_jwt_identity()
    if identity['role'] != 'DOCTOR':
        return jsonify({'error': 'Doctor only'}), 403

    doctor_email = identity['email']
    record = Record.query.filter_by(id=record_id, doctor_email=doctor_email).first()
    
    if not record:
        return jsonify({"error": "Record not found"}), 404

    try:
        # Remove physical file if it exists
        if record.file_path and os.path.exists(record.file_path):
            os.remove(record.file_path)
            
        db.session.delete(record)
        db.session.commit()
        
        log_event(doctor_email, 'REVOKE_RECORD', f'Doctor revoked record: {record.filename}')
        return jsonify({"success": True, "message": "Record revoked successfully"})
    except Exception as e:
        logging.error(f"Revoke failed: {str(e)}")
        return jsonify({"error": "Failed to revoke record"}), 500


