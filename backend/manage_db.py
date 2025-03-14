from main import app, db
from models import Tweet

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")

if __name__ == "__main__":
    init_db() 