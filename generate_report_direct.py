import os
import sys
from pathlib import Path

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import app
from services.encryption_service import process_and_send

def generate_report():
    """Directly invokes the encryption pipeline to generate security reports."""
    print("--- Initializing Direct Encryption Pipeline ---")
    
    # Use the Flask app context to access config and services
    with app.app_context():
        # Define participants
        sender_email = "doctor@test.com"
        receiver_email = "patient@test.com"
        
        # Define path to a sample DICOM file
        sample_dicom_path = Path("sample_data/sample.dcm")
        if not sample_dicom_path.exists():
            print(f"Error: Sample DICOM file not found at {sample_dicom_path}")
            return

        print(f"Processing DICOM: {sample_dicom_path}")
        print(f"Sender: {sender_email}, Receiver: {receiver_email}")

        try:
            # Directly call the encryption service
            result = process_and_send(
                dicom_path=str(sample_dicom_path),
                sender_email=sender_email,
                receiver_email=receiver_email
            )
            print("--- Encryption Pipeline Complete ---")
            print(f"Secure package created at: {result.get('file')}")
            print("Security metrics and graphs should now be available.")

        except Exception as e:
            print(f"An error occurred during the encryption pipeline: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    generate_report()
