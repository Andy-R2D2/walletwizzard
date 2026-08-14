from app import db
from datetime import datetime, timezone


class Budget(db.Model):
    __tablename__ = 'budgets'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category   = db.Column(db.String(50), nullable=False)
    planned    = db.Column(db.Float,      nullable=False)
    month      = db.Column(db.Integer,    nullable=False)   # 1-12
    year       = db.Column(db.Integer,    nullable=False)
    created_at = db.Column(db.DateTime,
                           default=lambda: datetime.now(timezone.utc))

    # One budget per category per month per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'month', 'year',
                            name='unique_budget_per_category_month'),
    )

    def __repr__(self):
        return f'<Budget {self.category} ${self.planned} {self.month}/{self.year}>'