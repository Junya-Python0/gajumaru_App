from flask import Flask, redirect, render_template
import sqlite3
from datetime import date

app = Flask(__name__)

DB_NAME = "watering.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS watering (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watered_at DATE NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()

    row = conn.execute("""
        SELECT watered_at
        FROM watering
        ORDER BY watered_at DESC, id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if row:
        last_watered = row["watered_at"]
        watered_date = date.fromisoformat(last_watered)
        days_since = (date.today() - watered_date).days
    else:
        last_watered = "まだ記録がありません"
        days_since = None

    return render_template(
        "index.html",
        last_watered=last_watered,
        days_since=days_since
    )


@app.route("/water", methods=["POST"])
def water():
    today = date.today().isoformat()

    conn = get_db()

    conn.execute(
        "INSERT INTO watering (watered_at) VALUES (?)",
        (today,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)