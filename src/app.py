"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.

The application now stores activities, student records, and memberships in a
SQLite database so data persists across server restarts.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import sqlite3

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities"
)

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

db_file = current_dir / "database.sqlite"

INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

INITIAL_STUDENTS = {
    "michael@mergington.edu": {"name": "Michael", "grade": "11"},
    "daniel@mergington.edu": {"name": "Daniel", "grade": "12"},
    "emma@mergington.edu": {"name": "Emma", "grade": "10"},
    "sophia@mergington.edu": {"name": "Sophia", "grade": "11"},
    "john@mergington.edu": {"name": "John", "grade": "12"},
    "olivia@mergington.edu": {"name": "Olivia", "grade": "10"},
    "liam@mergington.edu": {"name": "Liam", "grade": "12"},
    "noah@mergington.edu": {"name": "Noah", "grade": "11"},
    "ava@mergington.edu": {"name": "Ava", "grade": "10"},
    "mia@mergington.edu": {"name": "Mia", "grade": "11"},
    "amelia@mergington.edu": {"name": "Amelia", "grade": "10"},
    "harper@mergington.edu": {"name": "Harper", "grade": "12"},
    "ella@mergington.edu": {"name": "Ella", "grade": "11"},
    "scarlett@mergington.edu": {"name": "Scarlett", "grade": "12"},
    "james@mergington.edu": {"name": "James", "grade": "10"},
    "benjamin@mergington.edu": {"name": "Benjamin", "grade": "11"},
    "charlotte@mergington.edu": {"name": "Charlotte", "grade": "12"},
    "henry@mergington.edu": {"name": "Henry", "grade": "11"}
}


def get_db_connection():
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                email TEXT PRIMARY KEY,
                name TEXT,
                grade TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_memberships (
                activity_name TEXT NOT NULL,
                student_email TEXT NOT NULL,
                PRIMARY KEY (activity_name, student_email),
                FOREIGN KEY(activity_name) REFERENCES activities(name) ON DELETE CASCADE,
                FOREIGN KEY(student_email) REFERENCES students(email) ON DELETE CASCADE
            )
            """
        )

        existing = conn.execute("SELECT 1 FROM activities LIMIT 1").fetchone()
        if existing:
            return

        for email, student in INITIAL_STUDENTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO students (email, name, grade) VALUES (?, ?, ?)",
                (email, student["name"], student["grade"])
            )

        for activity_name, details in INITIAL_ACTIVITIES.items():
            conn.execute(
                "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                (
                    activity_name,
                    details["description"],
                    details["schedule"],
                    details["max_participants"],
                ),
            )
            for email in details["participants"]:
                conn.execute(
                    "INSERT OR IGNORE INTO activity_memberships (activity_name, student_email) VALUES (?, ?)",
                    (activity_name, email),
                )


def get_activity_data() -> dict:
    with get_db_connection() as conn:
        activities = {}
        activity_rows = conn.execute(
            "SELECT name, description, schedule, max_participants FROM activities ORDER BY name"
        ).fetchall()

        for activity in activity_rows:
            participants = [
                row["student_email"]
                for row in conn.execute(
                    "SELECT student_email FROM activity_memberships WHERE activity_name = ? ORDER BY student_email",
                    (activity["name"],),
                ).fetchall()
            ]
            activities[activity["name"]] = {
                "description": activity["description"],
                "schedule": activity["schedule"],
                "max_participants": activity["max_participants"],
                "participants": participants,
            }

        return activities


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return get_activity_data()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with get_db_connection() as conn:
        activity = conn.execute(
            "SELECT name, max_participants FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        existing_participant = conn.execute(
            "SELECT 1 FROM activity_memberships WHERE activity_name = ? AND student_email = ?",
            (activity_name, email),
        ).fetchone()
        if existing_participant:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        count = conn.execute(
            "SELECT COUNT(*) AS total FROM activity_memberships WHERE activity_name = ?",
            (activity_name,),
        ).fetchone()["total"]
        if count >= activity["max_participants"]:
            raise HTTPException(status_code=400, detail="Activity is full")

        conn.execute(
            "INSERT OR IGNORE INTO students (email, name, grade) VALUES (?, ?, ?)",
            (email, None, None),
        )
        conn.execute(
            "INSERT INTO activity_memberships (activity_name, student_email) VALUES (?, ?)",
            (activity_name, email),
        )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with get_db_connection() as conn:
        activity = conn.execute(
            "SELECT name FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        membership = conn.execute(
            "SELECT 1 FROM activity_memberships WHERE activity_name = ? AND student_email = ?",
            (activity_name, email),
        ).fetchone()
        if not membership:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        conn.execute(
            "DELETE FROM activity_memberships WHERE activity_name = ? AND student_email = ?",
            (activity_name, email),
        )

    return {"message": f"Unregistered {email} from {activity_name}"}


if __name__ == "__main__":
    import uvicorn

    initialize_database()
    uvicorn.run(app, host="0.0.0.0", port=8000)
