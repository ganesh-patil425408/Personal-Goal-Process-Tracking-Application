# GoalFlow — Personal Goal & Focus Tracker

A Python Tkinter + MySQL productivity application.

## Features
- User registration and login
- Goal management
- Task management
- 30-minute focus + 5-minute break timer
- Focus-session tracking
- XP rewards
- Dynamic motivational messages after task completion
- Progress statistics
- Goal progress calculation
- Foundation for Android DND integration

## Setup

### 1. Install MySQL
Make sure MySQL Server is running.

### 2. Configure database
Open `database.py` and change:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "goalflow"
}
```

Replace `YOUR_MYSQL_PASSWORD` with your MySQL password.

### 3. Install Python package

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

The application creates the `goalflow` database and tables automatically.

## Focus cycle

- 30 minutes Focus
- 5 minutes Break
- Repeat

## XP

- Complete Task: +10 XP
- Complete Focus Session: +20 XP

## Future enhancement

Connect an Android companion app using a secure local/API connection to control Android Do Not Disturb after the user grants DND permission.
