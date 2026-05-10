from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests

app = Flask(__name__)

BASE_URL = "http://host.docker.internal:5000/api"
API_KEY = "aleem"


def check_reminders():
    try:
        now = datetime.now().strftime("%H:%M")
        print(f"Checking reminders at {now}")

        # 1. Get users
        res = requests.get(f"{BASE_URL}/users/", headers={"X-API-Key": API_KEY})

        if res.status_code != 200:
            print("Failed to fetch users")
            return

        users = res.json()

        for u in users:

            # 2. Follow HATEOAS link (correct REST approach)
            habits_url = u["_links"]["habits"]["href"]

            full_url = f"http://host.docker.internal:5000/api/{habits_url}"

            res_h = requests.get(full_url, headers={"X-API-Key": API_KEY})
            if res_h.status_code != 200:
                continue

            habits = res_h.json()

            for h in habits:

                habit_name = h.get("name")
                reminder_time = h.get("reminder_time")

                if reminder_time == now:
                    print(f"[REMINDER] {habit_name} -> {u['email']}")
                

    except Exception as e:
        print(f"Error: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, "interval", seconds=30)
scheduler.start()


@app.route("/")
def home():
    return "Reminder Service Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
