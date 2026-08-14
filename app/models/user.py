from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80),  unique=True, nullable=False)
    email            = db.Column(db.String(120), unique=True, nullable=False)
    password_hash    = db.Column(db.String(255), nullable=False)
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Starting balance — user decides at first login
    # start_from_zero: True  → balance starts at 0
    # start_from_zero: False → user provides current_balance
    start_from_zero  = db.Column(db.Boolean, default=True)
    current_balance  = db.Column(db.Float,   default=0.0)

    # Relationships
    incomes       = db.relationship('Income',       backref='user', lazy=True, cascade='all, delete-orphan')
    expenses      = db.relationship('Expense',      backref='user', lazy=True, cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    goals         = db.relationship('Goal',         backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'
