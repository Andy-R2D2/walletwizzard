from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.subscription import Subscription

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/subscriptions')
@login_required
def index():
    subs = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    total_monthly = sum(s.amount for s in subs if s.active and s.billing == 'monthly')
    total_yearly  = sum(s.amount / 12 for s in subs if s.active and s.billing == 'yearly')
    total         = round(total_monthly + total_yearly, 2)
    count_active  = sum(1 for s in subs if s.active)
    return render_template('subscription/index.html',
                           subs=subs,
                           total=total,
                           count_active=count_active)


@subscription_bp.route('/subscriptions/add', methods=['GET', 'POST'])
@login_required
def add():
    # Max 5 active subscriptions rule from the doc — warning only, not hard block
    active_count = Subscription.query.filter_by(user_id=current_user.id, active=True).count()

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        amount  = request.form.get('amount', '').strip()
        billing = request.form.get('billing', 'monthly')

        if not name or not amount:
            flash('Name and amount are required.', 'error')
            return render_template('subscription/add.html', active_count=active_count)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('subscription/add.html', active_count=active_count)

        sub = Subscription(
            user_id=current_user.id,
            name=name,
            amount=amount,
            billing=billing,
            active=True
        )
        db.session.add(sub)
        db.session.commit()

        if active_count >= 5:
            flash(f'{name} added — you now have more than 5 active subscriptions. Consider reviewing them to save money.', 'error')
        else:
            flash(f'{name} added!', 'success')

        return redirect(url_for('subscription.index'))

    return render_template('subscription/add.html', active_count=active_count)


@subscription_bp.route('/subscriptions/toggle/<int:id>', methods=['POST'])
@login_required
def toggle(id):
    sub = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    sub.active = not sub.active
    db.session.commit()
    status = 'activated' if sub.active else 'paused'
    flash(f'{sub.name} {status}.', 'success')
    return redirect(url_for('subscription.index'))


@subscription_bp.route('/subscriptions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    sub = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        sub.name    = request.form.get('name', '').strip()
        sub.billing = request.form.get('billing', 'monthly')

        try:
            sub.amount = float(request.form.get('amount', 0))
            if sub.amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'error')
            return render_template('subscription/edit.html', sub=sub)

        db.session.commit()
        flash('Subscription updated.', 'success')
        return redirect(url_for('subscription.index'))

    return render_template('subscription/edit.html', sub=sub)


@subscription_bp.route('/subscriptions/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    sub = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(sub)
    db.session.commit()
    flash(f'{sub.name} removed.', 'success')
    return redirect(url_for('subscription.index'))