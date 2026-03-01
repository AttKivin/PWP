import pytest 
from datetime import datetime, time, timezone
from sqlalchemy.exc import IntegrityError
from habithub.models import User, Habit, Reminder, Tracking

class TestUser:
    def test_create_user(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            assert User.query.count() == 1
            assert User.query.first().first_name == "Atte"

    def test_unique_email(self, app, db):
        with app.app_context():
            user1 = User(first_name="Atte", last_name="Kiviniemi", email="ak@example.com")
            user2 = User(first_name="John", last_name="Doe", email="ak@example.com")
            db.session.add(user1)
            db.session.commit()
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_update_user(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            user.first_name = "Updated"
            db.session.commit()
            assert User.query.first().first_name == "Updated"

    def test_delete_user(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            assert User.query.count() == 1
            db.session.delete(user)
            db.session.commit()
            assert User.query.count() == 0
    
    def test_missing_required_field(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi")  # Missing email
            db.session.add(user)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

class TestHabit:
    def test_create_habit(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            assert Habit.query.count() == 1

    def test_habit_user_relationship(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            assert habit.user.first_name == "Atte"

    def test_delete_habit(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            assert Habit.query.count() == 1
            db.session.delete(habit)
            db.session.commit()
            assert Habit.query.count() == 0

    def test_multiple_habits_one_user(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit1 = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            habit2 = Habit(name="Read a book", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit1)
            db.session.add(habit2)
            db.session.commit()
            assert Habit.query.count() == 2

class TestReminder:
    def test_create_reminder(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            reminder = Reminder(habit_id=habit.id, reminded_time=time(8, 0), creation_date=datetime.now(timezone.utc))
            db.session.add(reminder)
            db.session.commit()
            assert Reminder.query.count() == 1

    def test_reminder_habit_relationship(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            reminder = Reminder(habit_id=habit.id, reminded_time=time(8, 0), creation_date=datetime.now(timezone.utc))
            db.session.add(reminder)
            db.session.commit()
            assert reminder.habit.name == "Go to the gym"
    
    def test_delete_reminder(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            reminder = Reminder(habit_id=habit.id, reminded_time=time(8, 0), creation_date=datetime.now(timezone.utc))
            db.session.add(reminder)
            db.session.commit()
            assert Reminder.query.count() == 1
            db.session.delete(reminder)
            db.session.commit()
            assert Reminder.query.count() == 0

class TestTracking:
    def test_create_tracking(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            tracking = Tracking(habit_id=habit.id, log_time=datetime.now(timezone.utc))
            db.session.add(tracking)
            db.session.commit()
            assert Tracking.query.count() == 1
    
    def test_tracking_habit_relationship(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            tracking = Tracking(habit_id=habit.id, log_time=datetime.now(timezone.utc))
            db.session.add(tracking)
            db.session.commit()
            assert tracking.habit.name == "Go to the gym"

    def test_delete_tracking(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            tracking = Tracking(habit_id=habit.id, log_time=datetime.now(timezone.utc))
            db.session.add(tracking)
            db.session.commit()
            assert Tracking.query.count() == 1
            db.session.delete(tracking)
            db.session.commit()
            assert Tracking.query.count() == 0

    def test_multiple_trackers_one_habit(self, app, db):
        with app.app_context():
            user = User(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
            db.session.add(user)
            db.session.commit()
            habit = Habit(name="Go to the gym", active=True, creation_date=datetime.now(timezone.utc), user_id=user.id)
            db.session.add(habit)
            db.session.commit()
            tracking1 = Tracking(habit_id=habit.id, log_time=datetime.now(timezone.utc))
            tracking2 = Tracking(habit_id=habit.id, log_time=datetime.now(timezone.utc))
            db.session.add(tracking1)
            db.session.add(tracking2)
            db.session.commit()
            assert Tracking.query.count() == 2
