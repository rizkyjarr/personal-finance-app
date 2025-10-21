from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os
import urllib

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

# Create all tables
if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")