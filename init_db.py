from hello import app, db, User
from werkzeug.security import generate_password_hash, check_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()

    # Users
    Steven = User(username = "Steven10", password_hash=generate_password_hash("Steven123"))
    db.session.add(Steven)
    db.session.commit()

    
