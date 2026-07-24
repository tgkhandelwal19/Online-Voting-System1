from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # Role can be 'user' or 'admin'
    role = db.Column(db.String(20), default='user')
    password_hash = db.Column(db.String(128), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    
    # Relationship to Votes
    votes = db.relationship('Vote', backref='voter', lazy=True)

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100), nullable=False)
    agenda = db.Column(db.Text, nullable=True)
    
    # Relationship to Votes
    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ElectionSettings(db.Model):
    __tablename__ = 'election_settings'
    id = db.Column(db.Integer, primary_key=True)
    # Storing deadline as a string or DateTime. DateTime is better.
    deadline = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
