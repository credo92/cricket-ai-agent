"""
V6 Decision Intelligence Agent.

Simulates 3 candidate tweets, predicts engagement for each, chooses the best one.
Enables learning from misses when actual engagement is backfilled.
"""

from agents.writer_agent import generate_candidates
from services.engagement_predictor import predict_engagement


def run_decision(event: str, emotion: str, num_candidates: int = 3) -> tuple[str, int]:
    """
    Generate multiple candidates, score each, return the best tweet and its predicted score.

    Returns:
        (best_tweet_text, predicted_engagement_score)
    """
    candidates = generate_candidates(event, emotion, n=num_candidates)

    if not candidates:
        from agents.writer_agent import generate_post
        fallback = generate_post(event, emotion)
        score = predict_engagement(fallback, event, emotion)
        return fallback, score

    scored = []
    for text in candidates:
        score = predict_engagement(text, event, emotion)
        scored.append((text, score))

    best = max(scored, key=lambda x: x[1])
    return best[0], best[1]
