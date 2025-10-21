from flask import Flask, render_template, request, redirect, url_for, flash
from models import Session, Transaction
from datetime import datetime
import os

app = Flask(__name__)
# Secret key required for flashing messages (use env var in production)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

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
        # Validate and parse date (expecting YYYY-MM-DD from <input type="date">)
        date_str = request.form.get('date', '').strip()
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            date_val = date_obj.isoformat()  # store as 'YYYY-MM-DD'
        except ValueError:
            flash('Invalid date format. Please use the date picker.', 'error')
            return render_template('add.html')

        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount. Please enter a numeric value.', 'error')
            return render_template('add.html')

        # Category selection handling
        selected = (request.form.get('category_select') or '').strip()
        other = (request.form.get('category') or '').strip()
        # Determine stored category and other_category
        if selected and selected != 'Others':
            store_category = selected
            store_other = None
        elif selected == 'Others':
            store_category = 'Others'
            store_other = other or None
        else:
            # No selection from dropdown; take free-text if provided
            store_category = other or ''
            store_other = other or None

        new_transaction = Transaction(
            date=date_val,
            type=request.form.get('type', ''),
            category=store_category,
            other_category=store_other,
            merchant=request.form.get('merchant', ''),
            description=request.form.get('description', ''),
            payment_method=request.form.get('payment_method', ''),
            bank_name=request.form.get('bank_name', ''),
            amount=amount
        )

        # Use context-managed session
        session = Session()
        try:
            session.add(new_transaction)
            session.commit()
        except Exception:
            session.rollback()
            flash('Failed to save transaction. Try again.', 'error')
            return render_template('add.html')
        finally:
            session.close()

        return redirect(url_for('index'))
    
    return render_template('add.html')

# Edit transaction
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    session = Session()
    transaction = session.get(Transaction, id)

    if transaction is None:
        session.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Validate date
        date_str = request.form.get('date', '').strip()
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            transaction.date = date_obj.isoformat()
        except ValueError:
            flash('Invalid date format. Please use the date picker.', 'error')
            session.close()
            return render_template('edit.html', transaction=transaction)

        # Validate amount
        try:
            transaction.amount = float(request.form.get('amount', transaction.amount))
        except ValueError:
            flash('Invalid amount. Please enter a numeric value.', 'error')
            session.close()
            return render_template('edit.html', transaction=transaction)

        transaction.type = request.form.get('type', transaction.type)
        # Category handling: category_select is the dropdown; category is the free-text for Others/custom
        selected = (request.form.get('category_select') or '').strip()
        other = (request.form.get('category') or '').strip()
        if selected and selected != 'Others':
            transaction.category = selected
            transaction.other_category = None
        elif selected == 'Others':
            transaction.category = 'Others'
            transaction.other_category = other or None
        else:
            # No dropdown selection; if free-text provided, use it
            if other:
                transaction.category = other
                transaction.other_category = other

        transaction.merchant = request.form.get('merchant', transaction.merchant)
        transaction.description = request.form.get('description', transaction.description)
        transaction.payment_method = request.form.get('payment_method', transaction.payment_method)
        transaction.bank_name = request.form.get('bank_name', transaction.bank_name)

        try:
            session.commit()
        except Exception:
            session.rollback()
            flash('Failed to update transaction. Try again.', 'error')
            session.close()
            return render_template('edit.html', transaction=transaction)

        session.close()
        return redirect(url_for('index'))

    session.close()
    return render_template('edit.html', transaction=transaction)

# Delete transaction
@app.route('/delete/<int:id>')
def delete_transaction(id):
    session = Session()
    transaction = session.get(Transaction, id)
    if transaction is not None:
        try:
            session.delete(transaction)
            session.commit()
        except Exception:
            session.rollback()
            flash('Failed to delete transaction. Try again.', 'error')
    session.close()

    return redirect(url_for('index'))

# Local Testing
if __name__ == '__main__':
    print("=== Starting Flask server ===")
    app.run(debug=True, port=5001)

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8181))
#     app.run(host='0.0.0.0', port=port)