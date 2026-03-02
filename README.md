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
flask --app habithub seed or python scripts/seed_db.py
```

### Verify data
```bash
flask --app habithub check or python scripts/check_db.py
```

### Run the API
```bash
flask --app habithub run
```

### Test the API
```bash
pytest tests/
```

### Running linting
The project uses **pylint** to check for warnings and proper coding convention. There are some warnings
that should be ignored as stated in the delivery page. Those are disabled in **pyproject.toml**
```toml
[tool.pylint."MESSAGES CONTROL"]
disable = [
    "no-member",
    "import-outside-toplevel"
]
```

Additionally, a hook is defined in **pyproject.toml** file that injects the current working directory
when **pylint** runs. This is needed when **pylint** runs from the root directory of the project because
pylint shows a warning that **habithub** can not be imported in our files
```toml
[tool.pylint.main]
init-hook = "import sys, os; sys.path.append(os.getcwd())"
```

**Pylint** does not run recursively by default, which means the tool must be invoked from the terminal for each sub directory. The following commands were used to make sure that the score is above 9.0
```bash
pylint habithub
pylint habithub/resources
pylint tests
```




__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__


