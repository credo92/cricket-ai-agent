"""
V6 Decision Intelligence: predict engagement BEFORE posting.
Scores candidate tweets 0–100 so we can choose the best and later learn from misses.
"""

from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY
from openai_errors import handle_openai_rate_limit

client = OpenAI(api_key=OPENAI_API_KEY)


def predict_engagement(text: str, event: str, emotion: str) -> int:
    """
    Predict virality of a candidate tweet (0–100).
    Used to rank candidates; later we compare with actual engagement to learn.
    """
    prompt = f"""
You are judging how viral a cricket tweet will be on X.

Event: {event}
Emotion/narrative: {emotion}

Tweet to score:
"{text}"

Consider: punchiness, emotional pull, reply bait, relevance to the moment, length.
Reply with ONLY a number from 0 to 100 (no explanation).
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
    except RateLimitError as e:
        handle_openai_rate_limit(e)

    raw = r.choices[0].message.content.strip()
    # Strip any non-digit
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return 50
    score = min(100, max(0, int(digits[:3] if len(digits) > 2 else digits)))
    return score
