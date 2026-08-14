from app import db
from datetime import datetime, timezone
import math


class Goal(db.Model):
    __tablename__ = 'goals'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name             = db.Column(db.String(100), nullable=False)
    target_amount    = db.Column(db.Float,       nullable=False)
    saved_amount     = db.Column(db.Float,       default=0.0)
    target_months    = db.Column(db.Integer,     nullable=False)
    estimated_months = db.Column(db.Integer,     nullable=True)
    allocation_pct   = db.Column(db.Float,       default=0.0)  # % of monthly savings assigned
    achieved         = db.Column(db.Boolean,     default=False)
    created_at       = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    @property
    def remaining(self):
        return max(0.0, self.target_amount - self.saved_amount)

    @property
    def progress_pct(self):
        if self.target_amount == 0:
            return 100.0
        return round(min(100.0, (self.saved_amount / self.target_amount) * 100), 1)

    @property
    def monthly_target(self):
        if self.target_months == 0:
            return self.target_amount
        return round(self.target_amount / self.target_months, 2)

    def recalculate_eta(self, monthly_savings: float):
        if monthly_savings <= 0:
            self.estimated_months = None
            return
        months_needed = math.ceil(self.remaining / monthly_savings)
        self.estimated_months = months_needed

    def __repr__(self):
        return f'<Goal {self.name} ${self.target_amount}>'
