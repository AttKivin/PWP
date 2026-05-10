# Reminder Auxiliary Service

## Overview

This service is an auxiliary reminder service for the Habit Tracker API. It runs separately from the main API and automatically checks habit reminder times in the background.

The service uses Flask and APScheduler. Every 30 seconds, it sends HTTP requests to the main Habit Tracker API, retrieves users, follows the habit links from the user representations, retrieves each user's habits, and checks whether any habit reminder time matches the current time.

If a reminder time matches the current time, the service prints a reminder message to the console.

## Purpose of the Service

The reminder service is separated from the main API because reminder checking is a scheduled background task. The main Habit Tracker API should focus on storing and returning habit data when clients request it.

If reminder checking was handled directly inside the API server, the API would need to run scheduled background logic while also handling normal client requests. This could make the API harder to maintain and less reliable.

The client also should not be responsible for checking reminders because the client would need to stay open all the time. This auxiliary service can run independently and check reminders automatically.

## How the Service Communicates with the Main API

The service communicates with the main Habit Tracker API using HTTP requests.

Main API base URL used by the service:

```text
http://host.docker.internal:5000/api
```

API key header used in requests:

```text
X-API-Key: aleem
```

The service performs the following steps:

1. Gets all users from the main API.

```text
GET /api/users/
```

2. Reads the habit link from each user response.

```python
u["_links"]["habits"]["href"]
```

3. Sends another request to retrieve the user's habits.

4. Reads each habit's name and reminder time.

```text
name
reminder_time
```

5. Compares `reminder_time` with the current time in `HH:MM` format.

6. Prints a reminder message if the times match.

Example output:

```text
Checking reminders at 14:30
[REMINDER] Drink water -> user@example.com
```

## Requirements

- Python 3.13 or newer
- Flask
- APScheduler
- requests
- Running Habit Tracker API on port 5000

Python dependencies are listed in `requirements.txt`.

## Installation

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Connecting to the Main API

Before starting this service, the main Habit Tracker API must be running.

The service expects the main API to be available at:

```text
http://host.docker.internal:5000/api
```

```python
BASE_URL = "http://host.docker.internal:5000/api"
API_KEY = "aleem"
```

The service sends the API key in this request header:

```text
X-API-Key: aleem
```

If the service is run locally without Docker on the same machine as the API, edit `app.py` and change the base URL to:

```python
BASE_URL = "http://127.0.0.1:5000/api"
```

## Running the Reminder Service Locally

Run the service with:

```bash
python app.py
```

The service starts on:

```text
http://localhost:5001/
```

Opening this URL should show:

```text
Reminder Service Running
```

The background reminder check starts automatically when the service starts.

## Running with Docker

Build the Docker image:

```bash
docker build -t reminder-service .
```

Run the container:

```bash
docker run --rm -p 5001:5001 reminder-service
```


## Demonstration

To demonstrate the service:

1. Start the main Habit Tracker API on port 5000.
2. Start the reminder service on port 5001.
3. Make sure the API returns users from `/api/users/`.
4. Make sure each user response contains a habit link in `_links.habits.href`.
5. Make sure the habit response contains `name` and `reminder_time` fields.
6. Set one habit's `reminder_time` to the current time in `HH:MM` format.
7. Check the reminder service console output.

## Expected output:

```text
Checking reminders at 14:30
[REMINDER] Drink water -> user@example.com


