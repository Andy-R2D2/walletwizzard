from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense, EXPENSE_CATEGORIES
from app.models.budget  import Budget
from sqlalchemy import extract
from datetime import date, datetime

expense_bp = Blueprint('expense', __name__)


def get_budget_map(user_id):
    now = datetime.now()
    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=now.month,
        year=now.year
    ).all()
    return {b.category: b.planned for b in budgets}


def get_spent_map(user_id):
    now = datetime.now()
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == now.month,
        extract('year',  Expense.date) == now.year
    ).all()
    spent = {}
    for e in expenses:
        spent[e.category] = round(spent.get(e.category, 0) + e.amount_actual, 2)
    return spent


@expense_bp.route('/expenses')
@login_required
def index():
    expenses      = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total_actual  = sum(e.amount_actual for e in expenses)
    budget_map    = get_budget_map(current_user.id)
    spent_map     = get_spent_map(current_user.id)
    return render_template('expense/index.html',
                           expenses=expenses,
                           total_actual=total_actual,
                           budget_map=budget_map,
                           spent_map=spent_map,
                           categories=EXPENSE_CATEGORIES)


@expense_bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add():
    budget_map = get_budget_map(current_user.id)
    spent_map  = get_spent_map(current_user.id)

    if request.method == 'POST':
        category    = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        amount      = request.form.get('amount_actual', '').strip()
        date_str    = request.form.get('date', '').strip()

        if not category or not amount:
            flash('Category and amount are required.', 'error')
            return render_template('expense/add.html',
                                   categories=EXPENSE_CATEGORIES,
                                   budget_map=budget_map,
                                   spent_map=spent_map,
                                   today=date.today().isoformat())

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('expense/add.html',
                                   categories=EXPENSE_CATEGORIES,
                                   budget_map=budget_map,
                                   spent_map=spent_map,
                                   today=date.today().isoformat())

        entry_date = date.fromisoformat(date_str) if date_str else date.today()

        expense = Expense(
            user_id=current_user.id,
            category=category,
            description=description or None,
            amount_actual=amount,
            date=entry_date
        )
        db.session.add(expense)
        db.session.commit()

        # Check overspend against budget
        planned  = budget_map.get(category, 0)
        new_spent = spent_map.get(category, 0) + amount
        if planned > 0 and new_spent > planned:
            over = round(new_spent - planned, 2)
            flash(f'Expense added — but you are ${over} over your {category} budget this month!', 'error')
        elif planned == 0:
            flash(f'Expense added. Tip: set a budget for {category} to track overspending.', 'success')
        else:
            remaining = round(planned - new_spent, 2)
            flash(f'Expense added. ${remaining} remaining in your {category} budget.', 'success')

        return redirect(url_for('expense.index'))

    return render_template('expense/add.html',
                           categories=EXPENSE_CATEGORIES,
                           budget_map=budget_map,
                           spent_map=spent_map,
                           today=date.today().isoformat())


@expense_bp.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense    = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    budget_map = get_budget_map(current_user.id)
    spent_map  = get_spent_map(current_user.id)

    if request.method == 'POST':
        expense.category    = request.form.get('category', '').strip()
        expense.description = request.form.get('description', '').strip() or None
        date_str            = request.form.get('date', '').strip()

        try:
            expense.amount_actual = float(request.form.get('amount_actual', 0))
            if expense.amount_actual <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('expense/edit.html',
                                   expense=expense,
                                   categories=EXPENSE_CATEGORIES,
                                   budget_map=budget_map,
                                   spent_map=spent_map)

        if date_str:
            expense.date = date.fromisoformat(date_str)

        db.session.commit()
        flash('Expense updated.', 'success')
        return redirect(url_for('expense.index'))

    return render_template('expense/edit.html',
                           expense=expense,
                           categories=EXPENSE_CATEGORIES,
                           budget_map=budget_map,
                           spent_map=spent_map)


@expense_bp.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('expense.index'))