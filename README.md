# PWP SPRING 2026
# Habit Tracker Web API
# Group information
* Student 1. Aleem Ud Din, aaleemud24@student.oulu.fi
* Student 2. Abdulmomen Ghalkha, abdulmomen.ghalkha@oulu.fi
* Student 3. Atte Kiviniemi, atkivini22@student.oulu.fi
* Student 4. Hatem ElKharashy, hatem.elkharashy@student.oulu.fi

## Database 
### Requirements
All the dependencies are included in the "requirements.txt" file. A simple working environment for this task is
```bash
python3 -m venv <venv_name>
Windows: .\<venv_name>\Scripts\activate or Linux/MacOS: source <venv_name>/bin/activate 
pip install -r requirements.txt
```
### Create tables 

```bash
flask --app habithub init-db
```

### Populate the database
```bash
flask --app habithub seed` or `python scripts/seed_db.py
```

### Verify data
```bash
flask --app habithub check` or `python scripts/check_db.py
```

### Run the API
```bash
flask --app habithub run
```

### Test the API
```bash
pytest tests/
```


__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__


