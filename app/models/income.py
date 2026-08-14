from app import db
from datetime import datetime, timezone


class Income(db.Model):
    __tablename__ = 'incomes'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    source      = db.Column(db.String(100), nullable=False)   # e.g. "Payroll", "Freelance"
    amount      = db.Column(db.Float,       nullable=False)
    date        = db.Column(db.Date,        nullable=False, default=lambda: datetime.now(timezone.utc).date())
    description = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Income {self.source} ${self.amount}>'
