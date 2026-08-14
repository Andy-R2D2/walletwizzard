from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.goal import Goal

goal_bp = Blueprint('goal', __name__)

MAX_GOALS = 5


@goal_bp.route('/goals')
@login_required
def index():
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.created_at.desc()).all()
    return render_template('goal/index.html', goals=goals, max_goals=MAX_GOALS)


@goal_bp.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add():
    count = Goal.query.filter_by(user_id=current_user.id, achieved=False).count()

    if count >= MAX_GOALS:
        flash(f'You can have a maximum of {MAX_GOALS} active goals. Complete or delete one first.', 'error')
        return redirect(url_for('goal.index'))

    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        target_amount = request.form.get('target_amount', '').strip()
        saved_amount  = request.form.get('saved_amount', '0').strip()
        target_months = request.form.get('target_months', '').strip()

        if not name or not target_amount or not target_months:
            flash('Name, target amount and target months are required.', 'error')
            return render_template('goal/add.html', count=count, max_goals=MAX_GOALS)

        try:
            target_amount = float(target_amount)
            saved_amount  = float(saved_amount) if saved_amount else 0.0
            target_months = int(target_months)
            if target_amount <= 0 or target_months <= 0:
                raise ValueError
        except ValueError:
            flash('Please enter valid numbers.', 'error')
            return render_template('goal/add.html', count=count, max_goals=MAX_GOALS)

        goal = Goal(
            user_id=current_user.id,
            name=name,
            target_amount=target_amount,
            saved_amount=saved_amount,
            target_months=target_months,
            estimated_months=target_months
        )
        db.session.add(goal)
        db.session.commit()
        flash(f'Goal "{name}" created!', 'success')
        return redirect(url_for('goal.index'))

    return render_template('goal/add.html', count=count, max_goals=MAX_GOALS)


@goal_bp.route('/goals/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        goal.name         = request.form.get('name', '').strip()
        saved             = request.form.get('saved_amount', '').strip()
        target_months     = request.form.get('target_months', '').strip()

        try:
            goal.target_amount = float(request.form.get('target_amount', 0))
            goal.saved_amount  = float(saved) if saved else 0.0
            goal.target_months = int(target_months) if target_months else goal.target_months
            if goal.target_amount <= 0:
                raise ValueError
        except ValueError:
            flash('Please enter valid numbers.', 'error')
            return render_template('goal/edit.html', goal=goal)

        if goal.saved_amount >= goal.target_amount:
            goal.achieved = True
            flash(f'Goal "{goal.name}" marked as achieved!', 'success')
        else:
            goal.achieved = False

        db.session.commit()
        flash('Goal updated.', 'success')
        return redirect(url_for('goal.index'))

    return render_template('goal/edit.html', goal=goal)


@goal_bp.route('/goals/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    goal = Goal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash(f'Goal "{goal.name}" deleted.', 'success')
    return redirect(url_for('goal.index'))