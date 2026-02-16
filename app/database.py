import sqlite3

conn = sqlite3.connect("data/learning.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS posts(
    id TEXT,
    text TEXT,
    emotion TEXT,
    narrative TEXT,
    score INTEGER DEFAULT 0,
    predicted_score INTEGER,
    actual_likes INTEGER,
    actual_retweets INTEGER,
    engagement_fetched_at TEXT
)
""")

# V6: add new columns if table already existed
for col, typ in [
    ("predicted_score", "INTEGER"),
    ("actual_likes", "INTEGER"),
    ("actual_retweets", "INTEGER"),
    ("engagement_fetched_at", "TEXT"),
]:
    try:
        c.execute(f"ALTER TABLE posts ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError:
        pass  # column already exists

conn.commit()
