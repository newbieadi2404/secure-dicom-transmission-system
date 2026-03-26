from secure_med_trans.transmission.email_receiver import EmailReceiver
from secure_med_trans.decrypt_main import decrypt_pipeline


def run():
    email_user = input("Email: ")
    password = input("App Password: ")

    receiver = EmailReceiver()

    file_path = receiver.fetch_latest_package(email_user, password)

    if file_path:
        print(f"📥 Downloaded: {file_path}")
        print("🔓 Starting decryption...")

        decrypt_pipeline(file_path)

    else:
        print("❌ No valid package found")


if __name__ == "__main__":
    run()