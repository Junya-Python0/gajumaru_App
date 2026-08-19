import os
import sqlite3
import requests
from datetime import date
from dotenv import load_dotenv


DB_NAME = "watering.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_watering_interval():
    conn = get_db()

    row = conn.execute("""
        SELECT watering_interval_days
        FROM settings
        WHERE id = 1
    """).fetchone()

    conn.close()

    return row["watering_interval_days"]


def get_last_watered():
    conn = get_db()

    row = conn.execute("""
        SELECT watered_at
        FROM watering
        ORDER BY watered_at DESC, id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if row is None:
        return None

    return date.fromisoformat(row["watered_at"])


def is_watering_due():
    last_watered = get_last_watered()

    # 一度も水やりしていない場合
    if last_watered is None:
        return False

    watering_interval = get_watering_interval()

    days_since = (date.today() - last_watered).days

    return days_since >= watering_interval


def send_discord_notification():
    load_dotenv()

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("DISCORD_WEBHOOK_URLが設定されていません")
        return

    last_watered = get_last_watered()
    watering_interval = get_watering_interval()

    days_since = (date.today() - last_watered).days

    message = (
        "🌱 ガジュマルCare\n\n"
        "そろそろ水やりのタイミングです。\n\n"
        f"最後の水やり：{last_watered}\n"
        f"経過日数：{days_since}日\n"
        f"水やり間隔：{watering_interval}日"
    )

    response = requests.post(
        webhook_url,
        json={
            "content": message
        }
    )

    if response.status_code == 204:
        print("Discord通知成功！")
    else:
        print(f"通知失敗: {response.status_code}")
        print(response.text)


if __name__ == "__main__":

    if is_watering_due():
        print("水やり期限です。Discord通知を送信します。")
        send_discord_notification()
    else:
        print("まだ水やり期限ではありません。")