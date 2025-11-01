from flask import Flask, render_template, request, redirect, url_for, flash, abort
from models import Session, Transaction, Category
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
# Secret key required for flashing messages (use env var in production)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

ALLOWED_TYPES = {"Income", "Expense"}


def _load_categories_context():
    """Load categories for both types to populate dropdowns in forms."""
    s = Session()
    try:
        categories_income = (
            s.query(Category)
            .filter(Category.type == 'Income')
            .order_by(Category.name)
            .all()
        )
        categories_expense = (
            s.query(Category)
            .filter(Category.type == 'Expense')
            .order_by(Category.name)
            .all()
        )
        return {
            'categories_income': categories_income,
            'categories_expense': categories_expense,
        }
    finally:
        s.close()

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
            return render_template('add.html', **_load_categories_context())

        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount. Please enter a numeric value.', 'error')
            return render_template('add.html', **_load_categories_context())

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
            return render_template('add.html', **_load_categories_context())
        finally:
            session.close()

        return redirect(url_for('index'))
    
    # GET: render form with categories
    return render_template('add.html', **_load_categories_context())

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
            return render_template('edit.html', transaction=transaction, **_load_categories_context())

        # Validate amount
        try:
            transaction.amount = float(request.form.get('amount', transaction.amount))
        except ValueError:
            flash('Invalid amount. Please enter a numeric value.', 'error')
            session.close()
            return render_template('edit.html', transaction=transaction, **_load_categories_context())

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
            return render_template('edit.html', transaction=transaction, **_load_categories_context())

        session.close()
        return redirect(url_for('index'))

    session.close()
    return render_template('edit.html', transaction=transaction, **_load_categories_context())


# ===== Categories Master Data =====

@app.route('/categories')
def list_categories():
    s = Session()
    try:
        filter_type = (request.args.get('type') or '').strip().capitalize()
        q = s.query(Category)
        if filter_type in ALLOWED_TYPES:
            q = q.filter(Category.type == filter_type)
        categories = q.order_by(Category.type, Category.name).all()
        return render_template('categories.html', categories=categories, filter_type=filter_type)
    finally:
        s.close()


@app.route('/categories/new', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        ctype = (request.form.get('type') or '').strip().capitalize()
        name = (request.form.get('name') or '').strip()

        if ctype not in ALLOWED_TYPES:
            flash('Type must be Income or Expense.', 'error')
            return render_template('category_form.html', category=None)
        if not name:
            flash('Name is required.', 'error')
            return render_template('category_form.html', category=None)

        s = Session()
        try:
            # prevent duplicates
            exists = s.query(Category).filter_by(type=ctype, name=name).first()
            if exists:
                flash('Category already exists for that type.', 'error')
                return render_template('category_form.html', category=None)

            s.add(Category(type=ctype, name=name))
            s.commit()
            flash('Category created.', 'success')
            return redirect(url_for('list_categories', type=ctype))
        except IntegrityError:
            s.rollback()
            flash('Category already exists.', 'error')
            return render_template('category_form.html', category=None)
        finally:
            s.close()

    return render_template('category_form.html', category=None)


@app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
def edit_category(id):
    s = Session()
    category = s.get(Category, id)
    if category is None:
        s.close()
        return redirect(url_for('list_categories'))

    if request.method == 'POST':
        ctype = (request.form.get('type') or '').strip().capitalize()
        name = (request.form.get('name') or '').strip()

        if ctype not in ALLOWED_TYPES:
            flash('Type must be Income or Expense.', 'error')
            s.close()
            return render_template('category_form.html', category=category)
        if not name:
            flash('Name is required.', 'error')
            s.close()
            return render_template('category_form.html', category=category)

        try:
            # check duplicate other than self
            dup = (
                s.query(Category)
                .filter(Category.type == ctype, Category.name == name, Category.id != id)
                .first()
            )
            if dup:
                flash('Another category with that name and type exists.', 'error')
                s.close()
                return render_template('category_form.html', category=category)

            category.type = ctype
            category.name = name
            s.commit()
            flash('Category updated.', 'success')
            s.close()
            return redirect(url_for('list_categories', type=ctype))
        except IntegrityError:
            s.rollback()
            flash('Category already exists.', 'error')
            s.close()
            return render_template('category_form.html', category=category)

    s.close()
    return render_template('category_form.html', category=category)


@app.route('/categories/<int:id>/delete', methods=['POST'])
def delete_category(id):
    s = Session()
    cat = s.get(Category, id)
    if cat is None:
        s.close()
        return redirect(url_for('list_categories'))
    try:
        ctype = cat.type
        s.delete(cat)
        s.commit()
        flash('Category deleted.', 'success')
    except Exception:
        s.rollback()
        flash('Failed to delete category.', 'error')
    finally:
        s.close()
    return redirect(url_for('list_categories', type=ctype))


@app.route('/categories/seed', methods=['POST'])
def seed_categories():
    # Optional dev helper; hide in non-debug if you prefer
    if not app.debug:
        return abort(404)
    from models import seed_default_categories
    try:
        seed_default_categories(Session)
        flash('Default categories seeded.', 'success')
    except Exception as e:
        flash(f'Failed to seed categories: {e}', 'error')
    return redirect(url_for('list_categories'))

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