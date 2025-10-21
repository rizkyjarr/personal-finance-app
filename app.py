from flask import Flask, render_template, request, redirect, url_for
from models import Session, Transaction
from datetime import datetime
import os

app = Flask(__name__)

# Home page - View all transactions
@app.route('/')
def index():
    session = Session()
    transactions = session.query(Transaction).order_by(Transaction.id.desc()).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'Income')
    total_expense = sum(t.amount for t in transactions if t.type == 'Expense')
    balance = total_income - total_expense
    
    session.close()
    return render_template('index.html', 
                         transactions=transactions,
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance)

# Add new transaction page
@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        session = Session()
        
        new_transaction = Transaction(
            date=request.form['date'],
            type=request.form['type'],
            category=request.form['category'],
            merchant=request.form['merchant'],
            description=request.form['description'],
            payment_method=request.form['payment_method'],
            bank_name=request.form['bank_name'],
            amount=float(request.form['amount'])
        )
        
        session.add(new_transaction)
        session.commit()
        session.close()
        
        return redirect(url_for('index'))
    
    return render_template('add.html')

# Edit transaction
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    session = Session()
    transaction = session.query(Transaction).get(id)
    
    if request.method == 'POST':
        transaction.date = request.form['date']
        transaction.type = request.form['type']
        transaction.category = request.form['category']
        transaction.merchant = request.form['merchant']
        transaction.description = request.form['description']
        transaction.payment_method = request.form['payment_method']
        transaction.bank_name = request.form['bank_name']
        transaction.amount = float(request.form['amount'])
        
        session.commit()
        session.close()
        
        return redirect(url_for('index'))
    
    session.close()
    return render_template('edit.html', transaction=transaction)

# Delete transaction
@app.route('/delete/<int:id>')
def delete_transaction(id):
    session = Session()
    transaction = session.query(Transaction).get(id)
    session.delete(transaction)
    session.commit()
    session.close()
    
    return redirect(url_for('index'))

#Local Testing
# if __name__ == '__main__':
#     print("=== Starting Flask server ===")
#     app.run(debug=True, port=5001)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8181))
    app.run(host='0.0.0.0', port=port)