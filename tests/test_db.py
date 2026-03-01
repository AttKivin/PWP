import pytest
import tempfile
import os
from datetime import datetime, time, timedelta, UTC
from habithub import db, create_app
from habithub.models import User, Habit, Reminder, Tracking

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app()
    
    ctx = app.app_context()
    ctx.push()

    db.create_all()

    yield db

    db.session.rollback()
    db.drop_all()
    db.session.remove()
    ctx.pop()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_user(first_name, last_name, email):
    return User(first_name=first_name, last_name=last_name, email=email)

def _get_habit(name, user):
    return Habit(name=name, user=user)

def _get_reminder(time, habit):
    return Reminder(reminded_time=time, habit=habit)

def _get_tracking(time, habit):
    return Tracking(log_time=time, habit=habit)

def test_create_user(db_handle):
    """
    Test the creation of one user successfully
    """

    john = _get_user("John", "Doe", "john.doe@example.com")
    db.session.add(john)
    db.session.commit()

    assert User.query.count() == 1
    assert User.query.first().first_name == "John"
    assert User.query.first().last_name == "Doe"
    assert User.query.first().email == "john.doe@example.com"

def test_create_habit(db_handle):
    """
    Test the creation of one habit for a user
    """

    john = _get_user("John", "Doe", "john.doe@example.com")
    habit = _get_habit("Swimming", john)

    db.session.add(habit)
    db.session.commit()

    assert Habit.query.count() == 1
    assert Habit.query.first().user == john
    assert Habit.query.first().active == True

def test_create_reminder(db_handle):
    """
    Test the creation of a reminder for a habit
    """

    john = _get_user("John", "Doe", "john.doe@example.com")
    habit = _get_habit("Swimming", john)
    reminder = _get_reminder(time(15, 30), habit)

    db.session.add(reminder)
    db.session.commit()

    assert User.query.count() == 1
    assert Habit.query.count() == 1
    assert Reminder.query.first().habit == habit
    assert Reminder.query.first().reminded_time == time(15, 30)

def test_create_tracking(db_handle):
    """
    Test the creation of a reminder for a habit
    """

    john = _get_user("John", "Doe", "john.doe@example.com")
    habit = _get_habit("Swimming", john)

    now = datetime.now()
    log_time = now - timedelta(days=1)
    tracking = _get_tracking(log_time, habit)

    db.session.add(tracking)
    db.session.commit()

    assert User.query.count() == 1
    assert Habit.query.count() == 1
    assert Tracking.query.count() == 1
    assert Tracking.query.first().habit == habit
    assert Tracking.query.first().log_time == log_time

def test_create_instances(db_handle):
    """
    Tests that we can create multiple users and add a list of habits to each
    of them. Moreover, we test creating reminders for habits and logging
    tracking time.
    """
    now = datetime.now(UTC)

    # demo users
    aleem = _get_user(first_name="Aleem", last_name="Ud Din", email="aleem.uddin@example.com")
    abdul = _get_user(first_name="Abdulmomen", last_name="Ghalkha", email="abdulmomen.ghalkha@example.com")
    atte  = _get_user(first_name="Atte", last_name="Kiviniemi", email="atte.kiviniemi@example.com")
    hatem = _get_user(first_name="Hatem", last_name="ElKharashy", email="hatem.elkharashy@example.com")

    db.session.add_all([aleem, abdul, atte, hatem])
    db.session.commit()

    # a small set of habits 
    habit_list = ["Gym", "Swimming", "Running", "Study", "Drink Water"]

    # create habits for each user
    users = [aleem, abdul, atte, hatem]
    for u in users:
        for hname in habit_list:
            db.session.add(_get_habit(
                name=hname,
                user=u
            ))
    db.session.commit()

    # grab a few habits so we can attach reminders
    aleem_gym = Habit.query.filter_by(user_id=aleem.id, name="Gym").first()
    aleem_study = Habit.query.filter_by(user_id=aleem.id, name="Study").first()
    abdul_swim = Habit.query.filter_by(user_id=abdul.id, name="Swimming").first()
    atte_water = Habit.query.filter_by(user_id=atte.id, name="Drink Water").first()
    hatem_run = Habit.query.filter_by(user_id=hatem.id, name="Running").first()

    # reminders
    db.session.add(_get_reminder(habit=aleem_gym, time=time(19, 0)))
    db.session.add(_get_reminder(habit=aleem_study, time=time(9, 0)))
    db.session.add(_get_reminder(habit=abdul_swim, time=time(18, 30)))
    db.session.add(_get_reminder(habit=atte_water, time=time(12, 0)))
    db.session.add(_get_reminder(habit=hatem_run, time=time(7, 30)))
    db.session.commit()

    # tracking logs:
    # Aleem gym: 5-day streak
    for i in range(5):
        db.session.add(_get_tracking(habit=aleem_gym, time=now - timedelta(days=i)))

    # Abdul swimming: missed one day (so it's not a perfect streak)
    db.session.add(_get_tracking(habit=abdul_swim, time=now))
    db.session.add(_get_tracking(habit=abdul_swim, time=now - timedelta(days=1)))
    db.session.add(_get_tracking(habit=abdul_swim, time=now - timedelta(days=3)))

    # Atte: small streak for water (3 days)
    for i in range(3):
        db.session.add(_get_tracking(habit=atte_water, time=now - timedelta(days=i)))

    # Hatem: only 2 logs
    db.session.add(_get_tracking(habit=hatem_run, time=now))
    db.session.add(_get_tracking(habit=hatem_run, time=now - timedelta(days=2)))

    db.session.commit()

    assert User.query.count() == 4
    assert Habit.query.count() == 20
    assert Tracking.query.count() == 13
    assert Reminder.query.count() == 5

    assert aleem_gym.user == aleem
    assert aleem_study.user == aleem
    assert abdul_swim.user == abdul
    assert atte_water.user == atte
    assert hatem_run.user == hatem

    assert len(aleem_gym.tracking_logs) == 5
    assert len(abdul_swim.tracking_logs) == 3
    assert len(atte_water.tracking_logs) == 3
    assert len(hatem_run.tracking_logs) == 2