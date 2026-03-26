import smtplib
from email.message import EmailMessage
from pathlib import Path
from config import OUTPUT_DIR


class EmailSender:

    def send_package(self, sender_email, password, receiver_email, file_path):
        msg = EmailMessage()
        msg["Subject"] = "Secure Medical Package"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        msg.set_content("Encrypted medical file attached.")

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Package not found: {file_path}")

        with open(path, "rb") as f:
            file_data = f.read()

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=path.name
        )

        try:
            print(f"🔄 Attempting to send email from {sender_email} to {receiver_email}...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender_email, password)
                smtp.send_message(msg)

            print(f"✅ Email sent successfully to {receiver_email}")

        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            raise e