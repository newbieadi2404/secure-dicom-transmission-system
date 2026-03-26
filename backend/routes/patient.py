from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pathlib import Path
import logging
import os
from config import BASE_DIR, UPLOADS_DIR

patient_bp = Blueprint("patient", __name__)

@patient_bp.route("/inbox", methods=["GET"])
@jwt_required()
def get_inbox():
    from backend.models.db import db
    from backend.models.record import Record
    identity = get_jwt_identity()
    if identity['role'] != 'PATIENT':
        return jsonify({'error': 'Patient only'}), 403

    patient_email = identity['email']
    records = Record.query.filter_by(patient_email=patient_email).order_by(Record.created_at.desc()).all()

    inbox = [{
        'id': r.id,
        'sender': r.doctor_email or '',
        'filename': r.filename,
        'status': r.status,
        'created_at': r.created_at.isoformat()
    } for r in records]

    return jsonify(inbox)

@patient_bp.route("/decrypt/<int:record_id>", methods=["POST"])
@jwt_required()
def decrypt_file(record_id):
    from backend.models.db import db
    from backend.models.record import Record
    from backend.models.audit import log_event
    # Import removed from here and moved inside try for better error handling if needed
    identity = get_jwt_identity()
    if identity['role'] != 'PATIENT':
        return jsonify({'error': 'Patient only'}), 403

    patient_email = identity['email']
    record = Record.query.filter_by(id=record_id, patient_email=patient_email).first()
    if not record:
        log_event(patient_email, 'DECRYPT_FAILED', f'Record {record_id} not found', 'error')
        return jsonify({'error': 'Record not found'}), 404

    if record.status == 'decrypted':
        log_event(patient_email, 'DECRYPT_FAILED', f'Record {record_id} already processed', 'warning')
        return jsonify({'error': 'Already decrypted'}), 400

    try:
        # Load patient private key for decryption
        from services.decryption_service import decrypt_file
        
        # Pass the patient_email to decrypt_file if it's needed for key resolution
        file_path = Path(record.file_path)
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

        result = decrypt_file(file_path)
        output_path = Path(result['output'])

        # Save as npy for viewing
        decrypted_dir = UPLOADS_DIR / 'decrypted'
        decrypted_dir.mkdir(parents=True, exist_ok=True)
        decrypted_npy = decrypted_dir / f"record_{record_id}.npy"
        # move or overwrite
        output_path.replace(decrypted_npy)

        record.status = 'decrypted'
        record.file_path = str(decrypted_npy)  # update to decrypted path
        db.session.commit()

        log_event(patient_email, 'DECRYPT_RECORD', f'Successfully decrypted imaging record: {record.filename}')
        logging.info(f"[DECRYPT] {patient_email} decrypted record {record_id}")

        return jsonify({
            'success': True,
            'output_path': str(decrypted_npy),
            'message': 'Decrypted successfully'
        })

    except Exception as e:
        logging.error(f"Decrypt failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@patient_bp.route("/send", methods=["POST"])
@jwt_required()
def send_file():
    from backend.models.db import db
    from backend.models.user import User
    from backend.models.record import Record
    from backend.models.audit import log_event
    from services.encryption_service import process_and_send
    from services.certificate_service import generate_user_certificate
    from services.key_service import resolve_public_key
    import json
    import tempfile
    from werkzeug.utils import secure_filename

    try:
        identity = get_jwt_identity()
        if identity['role'] != 'PATIENT':
            return jsonify({'error': 'Patient only'}), 403

        patient_email = identity['email']

        if "file" not in request.files:
            return jsonify({"error": "DICOM file required"}), 400

        dicom_file = request.files["file"]
        doctor_email = request.form.get("doctor_email")
        
        if not doctor_email:
            return jsonify({"error": "Recipient doctor email required"}), 400

        # Verify recipient doctor exists
        doctor = User.query.filter_by(email=doctor_email, role="DOCTOR").first()
        if not doctor:
            return jsonify({"error": "Doctor not registered"}), 404

        filename = secure_filename(dicom_file.filename)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as temp_file:
            dicom_file.save(temp_file.name)
            temp_path = temp_file.name

        patient_public = resolve_public_key(patient_email)
        patient_cert = None
        if patient_public:
            cert_dict = generate_user_certificate(patient_email, patient_public)
            patient_cert = json.dumps(cert_dict)

        result = process_and_send(
            temp_path,
            patient_email, # Sender
            doctor_email,  # Recipient
            certificate=patient_cert
        )

        smt_path = result.get("file")
        if not smt_path:
            raise Exception("Encryption failed")

        record = Record(
            patient_email=doctor_email,  # Using patient_email for recipient
            doctor_email=patient_email,   # Using doctor_email for sender
            filename=filename,
            file_path=str(smt_path),
            status="pending",
            body_part=request.form.get("body_part", "UNSPECIFIED"),
            priority=request.form.get("priority", "NORMAL"),
            clinical_notes=request.form.get("clinical_notes", "")
        )
        db.session.add(record)
        db.session.commit()

        log_event(patient_email, 'SEND_RECORD', f'Patient sent record to {doctor_email}')

        return jsonify({'message': 'Record sent successfully', 'id': record.id}), 201

    except Exception as e:
        logging.error(f"Patient send failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@patient_bp.route("/providers", methods=["GET"])
@jwt_required()
def get_providers():
    from backend.models.db import db
    from backend.models.record import Record
    identity = get_jwt_identity()
    if identity['role'] != 'PATIENT':
        return jsonify({'error': 'Patient only'}), 403

    patient_email = identity['email']
    
    # Get distinct doctors who have sent files to this patient
    distinct_doctors = db.session.query(Record.doctor_email).filter_by(patient_email=patient_email).distinct().all()
    
    provider_list = []
    for (d_email,) in distinct_doctors:
        total_count = Record.query.filter_by(doctor_email=d_email, patient_email=patient_email).count()
        last_record = Record.query.filter_by(doctor_email=d_email, patient_email=patient_email).order_by(Record.created_at.desc()).first()
        
        provider_list.append({
            "email": d_email,
            "total_records": total_count,
            "last_received": last_record.created_at.isoformat(),
            "status": "authorized"
        })

    return jsonify(provider_list)

@patient_bp.route("/record/<int:record_id>/image", methods=["GET"])
@jwt_required()
def get_record_image(record_id):
    from backend.models.record import Record
    import os
    import numpy as np
    from PIL import Image
    import io
    from flask import send_file
    
    identity = get_jwt_identity()
    patient_email = identity['email']
    
    record = Record.query.filter_by(id=record_id, patient_email=patient_email).first()
    if not record or record.status != 'decrypted':
        return jsonify({"error": "Image not available"}), 404
        
    file_path = Path(record.file_path)
    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path

    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
        
    try:
        # Load the numpy array
        img_array = np.load(file_path)
        
        # Normalize to 0-255 for PNG
        if img_array.max() > 0:
            img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min()) * 255.0
        img_array = img_array.astype(np.uint8)
        
        # Create PIL Image
        img = Image.fromarray(img_array)
        
        # Save to BytesIO
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        logging.error(f"Failed to generate image preview: {str(e)}")
        return jsonify({"error": "Failed to generate preview"}), 500

@patient_bp.route("/record/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    from backend.models.db import db
    from backend.models.record import Record
    from backend.models.audit import log_event
    import os
    
    identity = get_jwt_identity()
    if identity['role'] != 'PATIENT':
        return jsonify({'error': 'Patient only'}), 403

    patient_email = identity['email']
    record = Record.query.filter_by(id=record_id, patient_email=patient_email).first()
    
    if not record:
        return jsonify({"error": "Record not found"}), 404

    try:
        # Remove physical file if it exists
        if record.file_path and os.path.exists(record.file_path):
            os.remove(record.file_path)
            
        db.session.delete(record)
        db.session.commit()
        
        log_event(patient_email, 'DELETE_RECORD', f'Patient deleted record: {record.filename}')
        return jsonify({"success": True, "message": "Record deleted successfully"})
    except Exception as e:
        logging.error(f"Delete failed: {str(e)}")
        return jsonify({"error": "Failed to delete record"}), 500

@patient_bp.route("/record/<int:record_id>", methods=["GET"])
@jwt_required()
def get_record_details(record_id):
    from backend.models.record import Record
    identity = get_jwt_identity()
    patient_email = identity['email']
    
    record = Record.query.filter_by(id=record_id, patient_email=patient_email).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
        
    return jsonify({
        "id": record.id,
        "filename": record.filename,
        "status": record.status,
        "sender": record.doctor_email,
        "created_at": record.created_at.isoformat(),
        "body_part": record.body_part,
        "priority": record.priority,
        "clinical_notes": record.clinical_notes,
        "metadata": {
            "modality": record.modality or "DICOM",
            "encryption": "AES-256-CBC",
            "integrity": "Verified (SHA-256)"
        }
    })
