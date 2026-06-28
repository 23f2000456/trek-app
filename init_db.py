from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()


    if not User.query.filter_by(role='admin').first():
        admin = User(
            id=123,
            name='Admin',
            email='admin@trekkers.com',
            password=generate_password_hash('trekkers123'),
            role='admin',
            approval=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created.")
    else:
        print("Admin already exists.")