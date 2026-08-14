from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.income import Income
from datetime import date

income_bp = Blueprint('income', __name__)


@income_bp.route('/income')
@login_required
def index():
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    total = sum(i.amount for i in incomes)
    return render_template('income/index.html', incomes=incomes, total=total)


@income_bp.route('/income/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        source      = request.form.get('source', '').strip()
        amount      = request.form.get('amount', '').strip()
        date_str    = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()

        if not source or not amount:
            flash('Source and amount are required.', 'error')
            return render_template('income/add.html')

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('income/add.html')

        entry_date = date.fromisoformat(date_str) if date_str else date.today()

        income = Income(
            user_id=current_user.id,
            source=source,
            amount=amount,
            date=entry_date,
            description=description or None
        )
        db.session.add(income)
        db.session.commit()
        flash(f'Income of ${amount:.2f} added!', 'success')
        return redirect(url_for('income.index'))

    return render_template('income/add.html', today=date.today().isoformat())


@income_bp.route('/income/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    income = Income.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        income.source      = request.form.get('source', '').strip()
        income.description = request.form.get('description', '').strip() or None
        date_str           = request.form.get('date', '').strip()

        try:
            income.amount = float(request.form.get('amount', 0))
            if income.amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('income/edit.html', income=income)

        if date_str:
            income.date = date.fromisoformat(date_str)

        db.session.commit()
        flash('Income updated.', 'success')
        return redirect(url_for('income.index'))

    return render_template('income/edit.html', income=income)


@income_bp.route('/income/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    income = Income.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted.', 'success')
    return redirect(url_for('income.index'))