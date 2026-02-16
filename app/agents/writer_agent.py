from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY
from services.memory import load_style_examples
from openai_errors import handle_openai_rate_limit

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_post(event, emotion):

    style = load_style_examples()

    prompt = f"""
You are a viral cricket fan account on X.

Rules:
- Short punchy posts
- Emotional and opinionated
- Never sound like commentary
- Max 220 characters

Emotion: {emotion}
Event: {event}

Style examples:
{style}

Write ONE tweet.
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
    except RateLimitError as e:
        handle_openai_rate_limit(e)

    return r.choices[0].message.content.strip()


def generate_candidates(event, emotion, n=3):
    """Generate n distinct candidate tweets for decision layer to score and choose from."""
    style = load_style_examples()

    prompt = f"""
You are a viral cricket fan account on X.

Rules:
- Short punchy posts
- Emotional and opinionated
- Never sound like commentary
- Max 220 characters per tweet

Emotion: {emotion}
Event: {event}

Style examples:
{style}

Write exactly {n} DIFFERENT tweet options. Each must take a different angle or tone (e.g. hype vs fear, stats vs emotion).
Output ONLY the tweets, one per line, no numbering or labels.
"""

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
    except RateLimitError as e:
        handle_openai_rate_limit(e)

    raw = r.choices[0].message.content.strip()
    candidates = [line.strip() for line in raw.split("\n") if line.strip()]
    # Trim to n and ensure we have valid tweets (no "1." prefix etc.)
    out = []
    for c in candidates[:n]:
        c = c.lstrip("0123456789.)- ")
        if len(c) <= 280 and len(c) > 10:
            out.append(c)
    return out if len(out) >= 1 else [generate_post(event, emotion)]

