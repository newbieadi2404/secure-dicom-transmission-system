import imaplib
import email
from email.header import decode_header
from pathlib import Path


class EmailReceiver:

    def fetch_latest_package(self, email_user, password, download_folder="output"):
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, password)

        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        latest_id = mail_ids[-1]

        status, msg_data = mail.fetch(latest_id, "(RFC822)")

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        Path(download_folder).mkdir(exist_ok=True)

        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()

                if filename.endswith(".smt"):
                    filepath = Path(download_folder) / filename

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    print(f"✅ Downloaded: {filepath}")
                    return str(filepath)

        print("❌ No SMT file found in email")
        return None