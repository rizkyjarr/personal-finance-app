from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os
import urllib
from sqlalchemy import func

# Load environment variables
load_dotenv()

# Get ODBC connection string from .env
odbc_connection_string = os.getenv('SQL_CONNECTION_STRING')

# Convert ODBC connection string to SQLAlchemy format
# Encode it properly for SQLAlchemy
params = urllib.parse.quote_plus(odbc_connection_string)
SQL_CONNECTION_STRING = f"mssql+pyodbc:///?odbc_connect={params}"

print(f"Connecting to database...")

# Create engine
engine = create_engine(SQL_CONNECTION_STRING, echo=True)

# Session factory
Session = sessionmaker(bind=engine)

# Base class
Base = declarative_base()

# Define Transaction model
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)
    type = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)
    # Optional free-text category when user selects 'Others' in expense dropdown
    other_category = Column(String(100))
    merchant = Column(String(100))
    description = Column(String(200))
    payment_method = Column(String(20))
    bank_name = Column(String(50))
    amount = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Transaction {self.date} - {self.description} - Rp{self.amount}>"


class TimestampMixin:
    """Reusable timestamp columns (UTC by database default)."""
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Category(Base, TimestampMixin):
    """Master data for transaction categories by type (Income/Expense)."""

    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # constrained in application layer to one of {'Income', 'Expense'}
    type = Column(String(10), nullable=False)
    name = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint('type', 'name', name='uq_category_type_name'),
    )

    def __repr__(self):
        return f"<Category {self.type}:{self.name}>"


def seed_default_categories(session_factory: sessionmaker, *, echo: bool = True):
    """
    Idempotently seed default categories.
    Usage:
        from models import seed_default_categories, Session
        seed_default_categories(Session)
    """
    defaults = {
        'Income': [
            'Salary',
            'Reimbursement',
        ],
        'Expense': [
            'Food', 'Transportation', 'Social', 'Unexpected Cost', 'Housing',
            'Grooming', 'Sanitary', 'Electricity', 'Pulsa', 'Entertainment'
        ],
    }

    s = session_factory()
    try:
        created = 0
        for ctype, names in defaults.items():
            for name in names:
                exists = s.query(Category).filter_by(type=ctype, name=name).first()
                if not exists:
                    s.add(Category(type=ctype, name=name))
                    created += 1
        if created:
            s.commit()
            if echo:
                print(f"Seeded {created} categories")
        else:
            if echo:
                print("No categories to seed (already present)")
    except Exception as e:
        s.rollback()
        if echo:
            print(f"Seeding failed: {e}")
        raise
    finally:
        s.close()

# Create all tables
if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")