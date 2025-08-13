"""
WSGI entry point for Gunicorn
"""
from app import create_app, db

app = create_app()

# Ensure database tables exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables created/verified")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")

if __name__ == "__main__":
    app.run()