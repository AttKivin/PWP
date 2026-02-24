import click
from flask.cli import with_appcontext
from habithub import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)   
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    # Relationship to Habit 
    habits = db.relationship("Habit", back_populates="user")
    

class Habit(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")) 
    name = db.Column(db.String(64), nullable=False) 
    active = db.Column(db.Boolean, nullable=False) 
    creation_date = db.Column(db.DateTime, nullable=False)
    
    # Relationship back to User 
    user = db.relationship("User", back_populates="habits")
    
    # Relationship to Reminder 
    reminder = db.relationship("Reminder", back_populates="habit")

    # Relationship to Tracking
    tracking_logs = db.relationship("Tracking", back_populates="habit")


class Reminder(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE"))
    reminded_time = db.Column(db.Time, nullable=False) 
    creation_date = db.Column(db.DateTime, nullable=False) 
    
    # Relationship back to Habit 
    habit = db.relationship("Habit", back_populates="reminder")


class Tracking(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE")) 
    log_time = db.Column(db.DateTime, nullable=False) 
    # Relationship back to Habit 
    habit = db.relationship("Habit", back_populates="tracking_logs")

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
    print("Database create successfully")

@click.command("seed")
@with_appcontext
def seed_db_command():
    from scripts.seed_db import seed
    seed()

@click.command("check")
@with_appcontext
def check_db_command():
    from scripts.check_db import check
    check()