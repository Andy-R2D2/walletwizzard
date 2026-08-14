from app import db
from datetime import datetime, timezone


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name        = db.Column(db.String(100), nullable=False)   # e.g. "Netflix", "Spotify"
    amount      = db.Column(db.Float,       nullable=False)   # monthly cost
    billing     = db.Column(db.String(20),  default='monthly') # monthly / yearly
    active      = db.Column(db.Boolean,     default=True)
    created_at  = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Subscription {self.name} ${self.amount}>'
