import json
import pytest
from habithub import db as _db
from habithub.models import User, Habit, Reminder, Tracking
from datetime import datetime, time, timezone


# Helper functions for creating test data and making requests

def _get_user_json(first="Atte", last="Kiviniemi", email="atte@example.com"):
    return {"first_name": first, "last_name": last, "email": email}


def _get_habit_json(name="Go to the gym", active=True):
    return {"name": name, "active": active}


def _get_reminder_json(reminded_time="08:00"):
    return {"reminded_time": reminded_time}


def _get_tracking_json(log_time="2026-03-01T12:00:00Z"):
    return {"log_time": log_time}


def _create_user(client):
    """POST a user and return (response, user_id)."""
    resp = client.post("/api/users/", json=_get_user_json())
    user_id = User.query.first().id
    return resp, user_id


def _create_habit(client, user_id):
    """POST a habit and return (response, habit_id)."""
    resp = client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json())
    habit_id = Habit.query.first().id
    return resp, habit_id


class TestUserCollection:
    RESOURCE_URL = "/api/users/"

    def test_get_empty(self, client):
        """GET users when there are no users in the database."""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert resp.json == []

    def test_post_valid(self, client):
        """POST a valid user and verify it is created in the database."""
        resp = client.post(self.RESOURCE_URL, json=_get_user_json())
        assert resp.status_code == 201
        assert "Location" in resp.headers
        assert User.query.count() == 1

    def test_post_duplicate_email(self, client):
        """POST a user with an email that already exists in the database."""
        client.post(self.RESOURCE_URL, json=_get_user_json())
        resp = client.post(self.RESOURCE_URL, json=_get_user_json())
        assert resp.status_code == 409

    def test_post_missing_field(self, client):
        """POST with missing required field 'email'."""
        data = {"first_name": "Atte", "last_name": "Kiviniemi"}
        resp = client.post(self.RESOURCE_URL, json=data)
        assert resp.status_code == 400

    def test_post_wrong_content_type(self, client):
        """POST with non-JSON body."""
        resp = client.post(self.RESOURCE_URL, data="not json")
        assert resp.status_code == 415

    def test_get_populated(self, client):
        """GET users when there are multiple users in the database."""
        client.post(self.RESOURCE_URL, json=_get_user_json())
        client.post(self.RESOURCE_URL, json=_get_user_json(email="b@example.com"))
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert len(resp.json) == 2


class TestUserItem:

    def test_get(self, client):
        """GET a user and verify the returned data."""
        _, user_id = _create_user(client)
        resp = client.get(f"/api/users/{user_id}/")
        assert resp.status_code == 200
        assert resp.json["first_name"] == "Atte"

    def test_get_not_found(self, client):
        """GET a user that does not exist."""
        resp = client.get("/api/users/999/")
        assert resp.status_code == 404

    def test_put_valid(self, client):
        """PUT update a user with valid data and verify the changes in the database."""
        _, user_id = _create_user(client)
        data = _get_user_json(first="Updated", email="atte@example.com")
        resp = client.put(f"/api/users/{user_id}/", json=data)
        assert resp.status_code == 204
        assert _db.session.get(User, user_id).first_name == "Updated"

    def test_put_missing_field(self, client):
        """PUT with missing required field 'email'."""
        _, user_id = _create_user(client)
        resp = client.put(f"/api/users/{user_id}/", json={"first_name": "Only"})
        assert resp.status_code == 400

    def test_put_wrong_content_type(self, client):
        """PUT with non-JSON body."""
        _, user_id = _create_user(client)
        resp = client.put(f"/api/users/{user_id}/", data="not json")
        assert resp.status_code == 415

    def test_delete(self, client):
        """DELETE a user and verify it is removed from the database."""
        _, user_id = _create_user(client)
        resp = client.delete(f"/api/users/{user_id}/")
        assert resp.status_code == 204
        assert User.query.count() == 0

    def test_delete_not_found(self, client):
        """DELETE a user that does not exist."""
        resp = client.delete("/api/users/999/")
        assert resp.status_code == 404

    def test_put_duplicate_email(self, client):
        """PUT with an email that already belongs to another user."""
        _, user_id = _create_user(client)
        client.post("/api/users/", json=_get_user_json(email="other@example.com"))
        other_user_id = User.query.filter_by(email="other@example.com").first().id
        resp = client.put(
            f"/api/users/{other_user_id}/",
            json=_get_user_json(first="Other", last="User", email="atte@example.com"),
        )
        assert resp.status_code == 409


class TestHabitCollection:
    def test_get_empty(self, client):
        """GET habits for a user that has no habits."""
        _, user_id = _create_user(client)
        resp = client.get(f"/api/users/{user_id}/habits/")
        assert resp.status_code == 200
        assert resp.json == []

    def test_post_valid(self, client):
        """POST a valid habit and verify it is created in the database."""
        _, user_id = _create_user(client)
        resp = client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json())
        assert resp.status_code == 201
        assert "Location" in resp.headers
        assert Habit.query.count() == 1

    def test_post_missing_name(self, client):
        """POST a habit with a missing required field 'name'."""
        _, user_id = _create_user(client)
        resp = client.post(f"/api/users/{user_id}/habits/", json={"active": True})
        assert resp.status_code == 400

    def test_post_wrong_content_type(self, client):
        """POST with non-JSON body."""
        _, user_id = _create_user(client)
        resp = client.post(f"/api/users/{user_id}/habits/", data="not json")
        assert resp.status_code == 415

    def test_get_populated(self, client):
        """GET habits for a user that has multiple habits."""
        _, user_id = _create_user(client)
        client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json())
        client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json(name="Read"))
        resp = client.get(f"/api/users/{user_id}/habits/")
        assert resp.status_code == 200
        assert len(resp.json) == 2

    def test_post_invalid_user(self, client):
        """POST a habit for a non-existent user."""
        resp = client.post("/api/users/999/habits/", json=_get_habit_json())
        assert resp.status_code == 404


class TestHabitItem:

    def test_get(self, client):
        """GET a habit and verify the returned data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id}/")
        assert resp.status_code == 200
        assert resp.json["name"] == "Go to the gym"

    def test_get_not_found(self, client):
        """GET a habit that does not exist."""
        _, user_id = _create_user(client)
        resp = client.get(f"/api/users/{user_id}/habits/999/")
        assert resp.status_code == 404

    def test_get_wrong_owner(self, client):
        """GET a habit via a different user than it belongs to."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        client.post("/api/users/", json=_get_user_json(email="other@example.com"))
        other_user_id = User.query.filter_by(email="other@example.com").first().id
        resp = client.get(f"/api/users/{other_user_id}/habits/{habit_id}/")
        assert resp.status_code == 404

    def test_put_valid(self, client):
        """PUT update a habit with valid data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.put(f"/api/users/{user_id}/habits/{habit_id}/", json=_get_habit_json(name="Updated"))
        assert resp.status_code == 204
        assert _db.session.get(Habit, habit_id).name == "Updated"

    def test_put_missing_field(self, client):
        """PUT with missing required field 'name'."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.put(f"/api/users/{user_id}/habits/{habit_id}/", json={"active": False})
        assert resp.status_code == 400

    def test_put_wrong_content_type(self, client):
        """PUT with non-JSON body."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.put(f"/api/users/{user_id}/habits/{habit_id}/", data="not json")
        assert resp.status_code == 415

    def test_delete(self, client):
        """DELETE a habit and verify it is removed from the database."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.delete(f"/api/users/{user_id}/habits/{habit_id}/")
        assert resp.status_code == 204
        assert Habit.query.count() == 0


class TestReminderCollection:

    def _base_url(self, user_id, habit_id):
        return f"/api/users/{user_id}/habits/{habit_id}/reminders/"

    def test_get_empty(self, client):
        """GET reminders for a habit that has no reminders."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.get(self._base_url(user_id, habit_id))
        assert resp.status_code == 200
        assert resp.json == []

    def test_post_valid(self, client):
        """POST a valid reminder and verify it is created in the database."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), json=_get_reminder_json())
        assert resp.status_code == 201
        assert "Location" in resp.headers
        assert Reminder.query.count() == 1

    def test_post_missing_field(self, client):
        """POST a reminder with a missing required field."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), json={"extra": "data"})
        assert resp.status_code == 400

    def test_post_invalid_time_format(self, client):
        """POST with invalid time format for reminded_time."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), json={"reminded_time": "8 AM"})
        assert resp.status_code == 400

    def test_post_wrong_content_type(self, client):
        """POST with non-JSON body."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), data="not json")
        assert resp.status_code == 415


class TestReminderItem:

    def _create_reminder(self, client, user_id, habit_id):
        client.post(f"/api/users/{user_id}/habits/{habit_id}/reminders/", json=_get_reminder_json())
        return Reminder.query.first().id

    def test_get(self, client):
        """GET a reminder and verify the returned data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id)
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/")
        assert resp.status_code == 200
        assert resp.json["reminded_time"] == "08:00"

    def test_get_not_found(self, client):
        """GET a reminder that does not exist."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id}/reminders/999/")
        assert resp.status_code == 404

    def test_put_valid(self, client):
        """PUT update a reminder with valid data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id)
        resp = client.put(
            f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/",
            json=_get_reminder_json("09:30"),
        )
        assert resp.status_code == 204
        assert _db.session.get(Reminder, reminder_id).reminded_time == time(9, 30)

    def test_put_wrong_content_type(self, client):
        """PUT with non-JSON body."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id)
        resp = client.put(f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/", data="not json")
        assert resp.status_code == 415

    def test_delete(self, client):
        """Delete a reminder and verify it is removed from the database."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id)
        resp = client.delete(f"/api/users/{user_id}/habits/{habit_id}/reminders/{reminder_id}/")
        assert resp.status_code == 204
        assert Reminder.query.count() == 0

    def test_wrong_habit_for_reminder(self, client):
        """Access a reminder via a different habit than it belongs to."""
        _, user_id = _create_user(client)
        _, habit_id_1 = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id_1)
        client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json(name="Second"))
        habit_id_2 = Habit.query.filter_by(name="Second").first().id
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id_2}/reminders/{reminder_id}/")
        assert resp.status_code == 404

    def test_wrong_habit_owner(self, client):
        """Reminder belongs to habit of user1, accessed via user2's URL."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        reminder_id = self._create_reminder(client, user_id, habit_id)
        client.post("/api/users/", json=_get_user_json(email="other@example.com"))
        other_user_id = User.query.filter_by(email="other@example.com").first().id
        resp = client.get(f"/api/users/{other_user_id}/habits/{habit_id}/reminders/{reminder_id}/")
        assert resp.status_code == 404


class TestTrackingCollection:
    """Tests for the collection of tracking logs for a habit."""
    def _base_url(self, user_id, habit_id):
        return f"/api/users/{user_id}/habits/{habit_id}/tracking/"

    def test_get_empty(self, client):
        """GET tracking logs for a habit that has no logs."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.get(self._base_url(user_id, habit_id))
        assert resp.status_code == 200
        assert resp.json == []

    def test_post_valid(self, client):
        """POST a valid tracking log."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), json=_get_tracking_json())
        assert resp.status_code == 201
        assert "Location" in resp.headers
        assert Tracking.query.count() == 1

    def test_post_missing_field(self, client):
        """POST a tracking log with a missing required field."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), json={"extra": "data"})
        assert resp.status_code == 400

    def test_post_wrong_content_type(self, client):
        """POST with non-JSON body."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.post(self._base_url(user_id, habit_id), data="not json")
        assert resp.status_code == 415


class TestTrackingItem:
    """Tests for individual tracking logs."""
    def _create_tracking(self, client, user_id, habit_id):
        client.post(f"/api/users/{user_id}/habits/{habit_id}/tracking/", json=_get_tracking_json())
        return Tracking.query.first().id

    def test_get(self, client):
        """GET a tracking log and verify the returned data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id)
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking_id}/")
        assert resp.status_code == 200
        assert "log_time" in resp.json

    def test_get_not_found(self, client):
        """GET a tracking log that does not exist."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id}/tracking/999/")
        assert resp.status_code == 404

    def test_put_valid(self, client):
        """PUT update a tracking log with valid data."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id)
        resp = client.put(
            f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking_id}/",
            json=_get_tracking_json("2026-06-15T18:00:00Z"),
        )
        assert resp.status_code == 204

    def test_put_wrong_content_type(self, client):
        """PUT with non-JSON body."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id)
        resp = client.put(f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking_id}/", data="not json")
        assert resp.status_code == 415

    def test_delete(self, client):
        """DELETE a tracking log and verify it is removed from the database."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id)
        resp = client.delete(f"/api/users/{user_id}/habits/{habit_id}/tracking/{tracking_id}/")
        assert resp.status_code == 204
        assert Tracking.query.count() == 0

    def test_wrong_habit_for_tracking(self, client):
        """Access a tracking log via a different habit than it belongs to."""
        _, user_id = _create_user(client)
        _, habit_id_1 = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id_1)
        client.post(f"/api/users/{user_id}/habits/", json=_get_habit_json(name="Second"))
        habit_id_2 = Habit.query.filter_by(name="Second").first().id
        resp = client.get(f"/api/users/{user_id}/habits/{habit_id_2}/tracking/{tracking_id}/")
        assert resp.status_code == 404

    def test_wrong_habit_owner(self, client):
        """Tracking belongs to habit of user1, accessed via user2's URL."""
        _, user_id = _create_user(client)
        _, habit_id = _create_habit(client, user_id)
        tracking_id = self._create_tracking(client, user_id, habit_id)
        client.post("/api/users/", json=_get_user_json(email="other@example.com"))
        other_user_id = User.query.filter_by(email="other@example.com").first().id
        resp = client.get(f"/api/users/{other_user_id}/habits/{habit_id}/tracking/{tracking_id}/")
        assert resp.status_code == 404
