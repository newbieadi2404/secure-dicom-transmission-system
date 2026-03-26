import requests
import os
import time

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_flow():
    # 1. Login as Doctor
    print("--- Login as Doctor ---")
    login_data = {
        "email": "doctor@test.com",
        "password": "pass"
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.json()}")
        return
    
    doctor_token = resp.json()["token"]
    print("Doctor logged in successfully.")

    # 2. Upload DICOM
    print("\n--- Upload DICOM ---")
    # Path to a sample DICOM
    sample_dicom = "sample_data/sample.dcm"
    if not os.path.exists(sample_dicom):
        # try another one if not exists
        sample_dicom = "sample_data/dicom_viewer_0015/0015.DCM"
    
    if not os.path.exists(sample_dicom):
        print("No sample DICOM found.")
        return

    files = {
        'file': (os.path.basename(sample_dicom), open(sample_dicom, 'rb'), 'application/dicom')
    }
    data = {
        'patient_email': 'patient@test.com'
    }
    headers = {
        'Authorization': f'Bearer {doctor_token}'
    }
    
    resp = requests.post(f"{BASE_URL}/doctor/send", files=files, data=data, headers=headers)
    if resp.status_code != 201:
        print(f"Upload failed: {resp.json()}")
        return
    
    record_id = resp.json()["record_id"]
    print(f"DICOM uploaded and encrypted. Record ID: {record_id}")

    # 3. Login as Patient
    print("\n--- Login as Patient ---")
    login_data = {
        "email": "patient@test.com",
        "password": "pass"
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.json()}")
        return
    
    patient_token = resp.json()["token"]
    print("Patient logged in successfully.")

    # 4. Get Patient Inbox
    print("\n--- Get Patient Inbox ---")
    headers = {
        'Authorization': f'Bearer {patient_token}'
    }
    resp = requests.get(f"{BASE_URL}/patient/inbox", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get inbox: {resp.json()}")
        return
    
    inbox = resp.json()
    print(f"Inbox has {len(inbox)} records.")
    
    # Find our record
    target_record = next((r for r in inbox if r["id"] == record_id), None)
    if not target_record:
        print("Uploaded record not found in inbox.")
        return
    
    print(f"Found record: {target_record}")

    # 5. Decrypt Record
    print("\n--- Decrypt Record ---")
    resp = requests.post(f"{BASE_URL}/patient/decrypt/{record_id}", headers=headers)
    if resp.status_code != 200:
        print(f"Decryption failed: {resp.json()}")
        return
    
    print(f"Decryption successful: {resp.json()['message']}")
    print(f"Output path: {resp.json()['output_path']}")

import time

# ... (rest of the file)

if __name__ == "__main__":
    # ... (rest of the script)
    time.sleep(5)
    test_flow()
