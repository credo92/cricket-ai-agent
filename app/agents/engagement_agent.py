from database import conn
from datetime import datetime


def save_post(post_id, text, emotion, narrative, predicted_score=None):
    """Save posted tweet with optional V6 predicted score for learning from misses."""
    c = conn.cursor()
    c.execute("""
        INSERT INTO posts (id, text, emotion, narrative, predicted_score)
        VALUES (?, ?, ?, ?, ?)
    """, (post_id, text, emotion, narrative, predicted_score))
    conn.commit()


def update_actual_engagement(post_id, likes, retweets):
    """Backfill actual engagement so we can learn from prediction misses."""
    c = conn.cursor()
    # score = composite for ordering (e.g. likes + 2*retweets), normalized to 0–100 scale for comparison
    composite = likes + 2 * retweets
    c.execute("""
        UPDATE posts
        SET actual_likes = ?, actual_retweets = ?, score = ?, engagement_fetched_at = ?
        WHERE id = ?
    """, (likes, retweets, min(composite, 10000), datetime.utcnow().isoformat(), post_id))
    conn.commit()


def get_posts_without_engagement(limit=50):
    """Posts we've not yet backfilled with actual engagement (for learning job)."""
    c = conn.cursor()
    c.execute("""
        SELECT id FROM posts
        WHERE engagement_fetched_at IS NULL AND id IS NOT NULL
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return [row[0] for row in c.fetchall()]


def get_best_emotions():
    c = conn.cursor()
    c.execute("""
        SELECT emotion, AVG(score)
        FROM posts
        GROUP BY emotion
        ORDER BY AVG(score) DESC
    """)
    return c.fetchall()
