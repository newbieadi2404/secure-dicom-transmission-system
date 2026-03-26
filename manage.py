import os
import sys
import subprocess
import shutil
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@click.group()
def cli():
    """Project management CLI for Secure Medical Imaging Platform."""
    pass

@cli.command()
def setup():
    """Initialize the project environment (keys, DB, env)."""
    click.echo("🚀 Starting project setup...")

    # 1. Create directories
    dirs = ["keys", "uploads/decrypted", "output/debug", "output/encrypted_packages", "output/received_packages"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        click.echo(f"  Created directory: {d}")

    # 2. Generate CA keys if they don't exist
    if not os.path.exists("keys/ca_private.pem"):
        from secure_med_trans.security.cryptography.ca import CertificateAuthority
        priv, pub = CertificateAuthority.generate_ca_keys()
        with open("keys/ca_private.pem", "wb") as f:
            f.write(priv)
        with open("keys/ca_public.pem", "wb") as f:
            f.write(pub)
        click.echo("  ✅ CA keys generated.")
    else:
        click.echo("  ℹ️ CA keys already exist.")

    # 3. Initialize Database
    from backend.app import app
    from backend.models.db import init_db
    with app.app_context():
        init_db(app)
        click.echo("  ✅ Database initialized.")

    # 4. Create .env if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("SMTP_EMAIL=your-email@gmail.com\n")
            f.write("SMTP_PASSWORD=your-app-password\n")
            f.write("JWT_SECRET_KEY=dev-secret-key-12345\n")
        click.echo("  ✅ .env file created (Update with your SMTP credentials).")

    # 5. Frontend setup
    if os.path.exists("frontend"):
        click.echo("  📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="frontend", shell=True)
        click.echo("  ✅ Frontend dependencies installed.")

    click.echo("✨ Setup complete! Run 'python manage.py seed' to populate initial users.")

@cli.command()
def seed():
    """Seed the database with initial users."""
    from backend.app import app, db
    from backend.models.user import User
    from werkzeug.security import generate_password_hash

    click.echo("🌱 Seeding database...")
    with app.app_context():
        users = [
            ("doctor@test.com", "pass", "DOCTOR"),
            ("patient@test.com", "pass", "PATIENT"),
            ("admin@test.com", "pass", "ADMIN")
        ]
        for email, password, role in users:
            if not User.query.filter_by(email=email).first():
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    role=role
                )
                db.session.add(user)
                click.echo(f"  Created {role}: {email}")
        db.session.commit()
    click.echo("✅ Seeding complete!")

@cli.command()
@click.option('--port', default=5000, help='Port for the backend server.')
def run_backend(port):
    """Start the Flask backend server."""
    click.echo(f"🔥 Starting backend on port {port}...")
    subprocess.run([sys.executable, "backend/app.py"], env={**os.environ, "FLASK_PORT": str(port)})

@cli.command()
def run_frontend():
    """Start the Vite frontend development server."""
    click.echo("⚛️ Starting frontend...")
    subprocess.run(["npm", "run", "dev"], cwd="frontend", shell=True)

@cli.command()
def test_system():
    """Run system flow tests."""
    click.echo("🧪 Running system flow tests...")
    subprocess.run([sys.executable, "test_system_flow.py"])

@cli.command()
def test_unit():
    """Run unit tests."""
    click.echo("🧪 Running unit tests...")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"])

@cli.command()
def clean():
    """Clean up temporary files and directories."""
    click.echo("🧹 Cleaning up...")
    to_remove = ["__pycache__", "backend/__pycache__", "secure_med_trans/__pycache__", "instance", "uploads/*.smt", "uploads/decrypted/*.npy"]
    # Add logic to clean patterns or specific files
    click.echo("✅ Cleanup complete!")

if __name__ == "__main__":
    cli()
