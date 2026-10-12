import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin123",
    "database": "goalflow",
}


def connect():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    cfg = DB_CONFIG.copy()
    dbname = cfg.pop("database")
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {dbname}")
    cur.close()
    conn.close()
    conn = connect()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        xp INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS goals(
        goal_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, title VARCHAR(200) NOT NULL,
        description TEXT, category VARCHAR(80), priority VARCHAR(30),
        start_date DATE, target_date DATE, progress INT DEFAULT 0,
        status VARCHAR(30) DEFAULT 'Active',
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks(
        task_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, goal_id INT NOT NULL,
        task_name VARCHAR(255) NOT NULL, status VARCHAR(30) DEFAULT 'Pending',
        completed_at DATETIME NULL,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY(goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS focus_sessions(
        session_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, duration INT NOT NULL,
        completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE)""")
    conn.commit()
    cur.close()
    conn.close()


def register_user(name, email, password):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)",
        (name, email, password),
    )
    conn.commit()
    cur.close()
    conn.close()


def login_user(email, password):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM users WHERE email=%s AND password_hash=%s", (email, password)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def parse_date(value):
    if not value:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("Invalid date. Use YYYY-MM-DD, for example 2026-12-31.")


def add_goal(user_id, title, description, category, priority, target_date):
    target_date = parse_date(target_date)
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO goals
            (user_id, title, description, category, priority, start_date, target_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, title, description, category, priority,
             datetime.now().date(), target_date),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_goals(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM goals WHERE user_id=%s ORDER BY goal_id DESC", (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def complete_goal(user_id, goal_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT status FROM goals WHERE goal_id=%s AND user_id=%s", (goal_id, user_id)
    )
    goal = cur.fetchone()
    if not goal or goal["status"] == "Completed":
        cur.close()
        conn.close()
        return False
    cur.execute(
        "UPDATE goals SET status='Completed', progress=100 WHERE goal_id=%s AND user_id=%s",
        (goal_id, user_id),
    )
    cur.execute("UPDATE users SET xp=xp+50 WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True


def add_task(user_id, goal_id, task_name):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks(user_id,goal_id,task_name) VALUES(%s,%s,%s)",
        (user_id, goal_id, task_name),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_tasks(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT t.*, g.title goal_title FROM tasks t JOIN goals g ON t.goal_id=g.goal_id
                   WHERE t.user_id=%s ORDER BY t.task_id DESC""",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def complete_task(user_id, task_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM tasks WHERE task_id=%s AND user_id=%s", (task_id, user_id)
    )
    task = cur.fetchone()
    if not task or task["status"] == "Completed":
        cur.close()
        conn.close()
        return False
    cur.execute(
        "UPDATE tasks SET status='Completed', completed_at=NOW() WHERE task_id=%s",
        (task_id,),
    )
    cur.execute("UPDATE users SET xp=xp+10 WHERE user_id=%s", (user_id,))
    cur.execute(
        """UPDATE goals g SET progress=(
        SELECT COALESCE(ROUND(SUM(status='Completed')/COUNT(*)*100),0) FROM tasks WHERE goal_id=g.goal_id)
        WHERE g.goal_id=%s""",
        (task["goal_id"],),
    )
    cur.execute(
        """UPDATE goals SET status='Completed' WHERE goal_id=%s AND progress=100""",
        (task["goal_id"],),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def add_focus_session(user_id, duration):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO focus_sessions(user_id,duration) VALUES(%s,%s)",
        (user_id, duration),
    )
    cur.execute("UPDATE users SET xp=xp+20 WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_stats(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) goals FROM goals WHERE user_id=%s", (user_id,))
    goals = cur.fetchone()["goals"]
    cur.execute(
        "SELECT COUNT(*) completed_tasks FROM tasks WHERE user_id=%s AND status='Completed'",
        (user_id,),
    )
    ct = cur.fetchone()["completed_tasks"]
    cur.execute(
        "SELECT COALESCE(SUM(duration),0) focus_minutes FROM focus_sessions WHERE user_id=%s",
        (user_id,),
    )
    fm = cur.fetchone()["focus_minutes"]
    cur.execute("SELECT xp FROM users WHERE user_id=%s", (user_id,))
    xp = cur.fetchone()["xp"]
    cur.close()
    conn.close()
    return {"goals": goals, "completed_tasks": ct, "focus_minutes": fm, "xp": xp}