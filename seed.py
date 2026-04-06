import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.core.database import SessionLocal, Base, engine
from app.models.user import User, RoleEnum
from app.models.transaction import Transaction, TransactionType
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Check if admin already exists
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        logger.info("Creating initial admin user...")
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=RoleEnum.admin,
            is_active=True
        )
        db.add(admin)
        
    analyst = db.query(User).filter(User.email == "analyst@example.com").first()
    if not analyst:
        logger.info("Creating initial analyst user...")
        analyst = User(
            email="analyst@example.com",
            hashed_password=get_password_hash("analyst123"),
            role=RoleEnum.analyst,
            is_active=True
        )
        db.add(analyst)
        
    db.commit()
    db.refresh(admin)

    # Check if transactions exist
    if db.query(Transaction).count() == 0:
        logger.info("Seeding transactions...")
        categories_income = ["Salary", "Investments", "Freelance", "Gift"]
        categories_expense = ["Rent", "Groceries", "Utilities", "Entertainment", "Dining Out", "Transportation"]
        
        for _ in range(50):
            is_income = random.choice([True, False])
            db_obj = Transaction(
                amount=round(random.uniform(10.0, 5000.0), 2),
                type=TransactionType.income if is_income else TransactionType.expense,
                category=random.choice(categories_income) if is_income else random.choice(categories_expense),
                notes="Generated seed data",
                date=datetime.now() - timedelta(days=random.randint(0, 60)),
                owner_id=admin.id
            )
            db.add(db_obj)
        db.commit()
        logger.info("Successfully seeded database.")

def main() -> None:
    logger.info("Initializing database session")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Finished database initialization")

if __name__ == "__main__":
    main()
