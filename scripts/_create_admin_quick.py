"""Quick admin creation - no interactive input."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, Base
from app.auth import get_password_hash
from uuid import uuid4

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5432/agency_os")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

existing = db.query(User).filter(User.username == "admin").first()
if existing:
    existing.password_hash = get_password_hash("senha123")
    db.commit()
    print("✅ Senha do admin resetada para 'senha123'")
else:
    user = User(
        id=str(uuid4()),
        username="admin",
        email="admin@vyron.com",
        password_hash=get_password_hash("senha123"),
        role="admin",
    )
    db.add(user)
    db.commit()
    print("✅ Admin criado! user=admin / senha=senha123")

db.close()
