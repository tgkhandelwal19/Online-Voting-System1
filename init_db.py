from app import app
from models import db, User, ElectionSettings
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(voter_id='admin').first()
        if not admin:
            # Create default admin
            print("Creating default admin account...")
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(
                voter_id='admin',
                name='Election Administrator',
                role='admin',
                password_hash=hashed_password,
                has_voted=False
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin account created! (voter_id: 'admin', password: 'admin123')")
            
        settings = ElectionSettings.query.first()
        if not settings:
            print("Initializing election settings...")
            new_settings = ElectionSettings(is_active=True, deadline=None)
            db.session.add(new_settings)
            db.session.commit()
            print("Election settings initialized.")
            
        print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
