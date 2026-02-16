"""
V6 Learning from misses: backfill actual engagement and compare to predicted.
Run periodically (e.g. every 15 min) so the system learns which predictions were right/wrong.
"""

from x_client import get_tweet_engagement
from agents.engagement_agent import get_posts_without_engagement, update_actual_engagement
import time


def run_feedback_cycle(batch_size=20, delay_seconds=1):
    """
    Fetch engagement for recent posts that don't have it yet.
    Updates DB so we can analyze predicted_score vs actual (likes + 2*retweets) and improve.
    """
    post_ids = get_posts_without_engagement(limit=batch_size)
    updated = 0
    for post_id in post_ids:
        likes, retweets = get_tweet_engagement(post_id)
        if likes is not None:
            update_actual_engagement(post_id, likes, retweets)
            updated += 1
        time.sleep(delay_seconds)  # respect rate limits
    return updated
