from flask import Flask, redirect, render_template, request
import sqlite3
from datetime import date
from waitress import serve

app = Flask(__name__)

DB_NAME = "watering.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # 水やり履歴
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watering (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watered_at DATE NOT NULL
        )
    """)

    # 設定
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            watering_interval_days INTEGER NOT NULL
        )
    """)

    # 設定がまだ存在しない場合は初期値7日を登録
    conn.execute("""
        INSERT OR IGNORE INTO settings (id, watering_interval_days)
        VALUES (1, 7)
    """)

    conn.commit()
    conn.close()


def get_watering_interval():
    conn = get_db()

    row = conn.execute("""
        SELECT watering_interval_days
        FROM settings
        WHERE id = 1
    """).fetchone()

    conn.close()

    return row["watering_interval_days"]


def set_watering_interval(days):
    conn = get_db()

    conn.execute("""
        UPDATE settings
        SET watering_interval_days = ?
        WHERE id = 1
    """, (days,))

    conn.commit()
    conn.close()


# 水やり期限を判定
def is_watering_due():
    conn = get_db()

    # 最後の水やりを取得
    row = conn.execute("""
        SELECT watered_at
        FROM watering
        ORDER BY watered_at DESC, id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    # まだ一度も水やりしていない場合
    if row is None:
        return False

    last_watered = date.fromisoformat(row["watered_at"])

    # 設定した水やり間隔を取得
    watering_interval = get_watering_interval()

    # 水やりから経過した日数
    days_since = (date.today() - last_watered).days

    return days_since >= watering_interval


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

    watering_interval = get_watering_interval()

    # 水やり期限かどうか
    watering_due = is_watering_due()

    return render_template(
        "index.html",
        last_watered=last_watered,
        days_since=days_since,
        watering_interval=watering_interval,
        watering_due=watering_due
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


@app.route("/settings", methods=["POST"])
def settings():
    days = request.form.get("watering_interval_days", type=int)

    if days is not None and days > 0:
        set_watering_interval(days)

    return redirect("/")


if __name__ == "__main__":
    init_db()
    serve(app, host="0.0.0.0", port=5001)