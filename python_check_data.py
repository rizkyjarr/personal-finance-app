from models import Session, Transaction

session = Session()
transactions = session.query(Transaction).all()

print(f"Total transactions in database: {len(transactions)}")
for t in transactions:
    print(f"  - {t}")

session.close()