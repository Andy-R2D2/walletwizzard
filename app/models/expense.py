from app import db
from datetime import datetime, timezone

EXPENSE_CATEGORIES = [
    ('Food',          '🍔'),
    ('Transport',     '🚗'),
    ('Entertainment', '🎬'),
    ('Health',        '💊'),
    ('Education',     '📚'),
    ('Clothing',      '👕'),
    ('Housing',       '🏠'),
    ('Utilities',     '⚡'),
    ('Other',         '📦'),
]

# Just the names for quick lookups
CATEGORY_NAMES = [c[0] for c in EXPENSE_CATEGORIES]


class Expense(db.Model):
    __tablename__ = 'expenses'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category      = db.Column(db.String(50),  nullable=False)
    description   = db.Column(db.String(255), nullable=True)
    amount_actual = db.Column(db.Float,       nullable=False)
    date          = db.Column(db.Date,        nullable=False,
                              default=lambda: datetime.now(timezone.utc).date())
    created_at    = db.Column(db.DateTime,
                              default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Expense {self.category} ${self.amount_actual}>'
