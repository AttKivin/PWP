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
