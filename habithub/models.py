from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from sqlalchemy.engine import Engine
from sqlalchemy import event

# To be moved to the 9
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
    email = db.Column(db.String(128), nullable=False, unique=True) 
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


ctx = app.app_context()
ctx.push()
db.create_all()
ctx.pop()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
