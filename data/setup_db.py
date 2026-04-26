"""
Initializes the SQLite database with mock transaction history.
Run this once before using the agent: python data/setup_db.py
"""
import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "transactions.db")


def get_db_path():
    return DB_PATH


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT NOT NULL,
            amount          REAL NOT NULL,
            merchant        TEXT NOT NULL,
            category        TEXT NOT NULL,
            location        TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            is_fraud        INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] > 0:
        print("Database already populated, skipping seed.")
        conn.close()
        return

    merchants = {
        "groceries":  ["Whole Foods", "Trader Joe's", "Safeway", "Kroger"],
        "gas":        ["Shell", "Chevron", "BP", "ExxonMobil"],
        "restaurant": ["McDonald's", "Chipotle", "Starbucks", "Olive Garden"],
        "electronics":["Apple Store", "Best Buy", "Amazon", "Newegg"],
        "travel":     ["Delta Airlines", "Marriott", "Airbnb", "Expedia"],
        "atm":        ["ATM Withdrawal", "Cash Advance"],
        "online":     ["eBay", "Etsy", "Shopify Store", "Unknown Merchant"],
    }

    locations_normal = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX"]
    locations_risky  = ["Lagos, Nigeria", "Minsk, Belarus", "Unknown Location", "Bogotá, Colombia"]

    users = ["user_001", "user_002", "user_003"]
    rows = []

    base_time = datetime.now() - timedelta(days=90)
    for user in users:
        for day_offset in range(90):
            tx_count = random.randint(1, 4)
            for _ in range(tx_count):
                category = random.choice(list(merchants.keys()))
                merchant = random.choice(merchants[category])
                amount   = round(random.uniform(5, 200), 2)
                location = random.choice(locations_normal)
                ts       = (base_time + timedelta(days=day_offset,
                             hours=random.randint(8, 22))).strftime("%Y-%m-%d %H:%M:%S")
                rows.append((user, amount, merchant, category, location, ts, 0))

        # Inject fraudulent transactions
        for _ in range(5):
            category = random.choice(["electronics", "online", "atm"])
            merchant = random.choice(merchants[category])
            amount   = round(random.uniform(800, 5000), 2)
            location = random.choice(locations_risky)
            ts       = (base_time + timedelta(days=random.randint(0, 89),
                         hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
            rows.append((user, amount, merchant, category, location, ts, 1))

    cursor.executemany(
        "INSERT INTO transactions (user_id, amount, merchant, category, location, timestamp, is_fraud) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Database seeded with {len(rows)} transactions at {DB_PATH}")


if __name__ == "__main__":
    setup_database()
