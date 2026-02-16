"""
X (Twitter) API client — Viral-level v3.

Supports: single posts, threads, replies (banter), quote tweets,
tweet context for reply generation, and engagement metrics for learning.
"""
import time
import tweepy
from tweepy import Unauthorized
from config import (
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET,
)


def _check_credentials():
    """Ensure all X API credentials are set and not placeholders."""
    required = {
        "X_API_KEY": X_API_KEY,
        "X_API_SECRET": X_API_SECRET,
        "X_ACCESS_TOKEN": X_ACCESS_TOKEN,
        "X_ACCESS_SECRET": X_ACCESS_SECRET,
    }
    missing = [k for k, v in required.items() if not v or not str(v).strip()]
    if missing:
        raise ValueError(
            "Missing or empty X API credentials: {}. "
            "Set them in .env (see .env.example).".format(", ".join(missing))
        )
    placeholders = ("your-", "sk-your-")
    for name, value in required.items():
        if value and str(value).strip().lower().startswith(placeholders):
            raise ValueError(
                "{} looks like a placeholder. Replace with real values from "
                "https://developer.x.com/ (App → Keys and tokens).".format(name)
            )


_check_credentials()

# Twitter API v2 Client (required for create_tweet, get_tweet, threads, reply, quote)
client = tweepy.Client(
    consumer_key=X_API_KEY,
    consumer_secret=X_API_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_SECRET,
)


def _raise_401_help(original=None):
    msg = (
        "X API returned 401 Unauthorized. Posting requires the right app permissions and user tokens.\n\n"
        "Do these in order:\n"
        "1. Go to https://developer.x.com/ → your project → Settings.\n"
        "2. Under 'User authentication settings', set App permissions to 'Read and Write' (not Read only). Save.\n"
        "3. Open 'Keys and tokens'. Use the OAuth 1.0a section:\n"
        "   - X_API_KEY = API Key, X_API_SECRET = API Key Secret\n"
        "   - X_ACCESS_TOKEN = Access Token, X_ACCESS_SECRET = Access Token Secret\n"
        "   (Do NOT use the Bearer Token for X_ACCESS_TOKEN; that is read-only.)\n"
        "4. If you changed permissions, under 'Access token and secret' click 'Regenerate', then copy the new token and secret into .env.\n"
        "5. Restart the app. Tokens from before a permission change will not work."
    )
    if original is not None:
        raise RuntimeError(msg) from original
    raise RuntimeError(msg)


def _tweet_id_from_response(r):
    """Extract tweet id from create_tweet response (handles tweepy Response object)."""
    if not r or not r.data:
        return None
    d = r.data
    return getattr(d, "id", None) or (d.get("id") if isinstance(d, dict) else None)


# -----------------------------------------------------------------------------
# Single tweet (backward compatible)
# -----------------------------------------------------------------------------


def post_tweet(text, reply_to_id=None, quote_tweet_id=None):
    """
    Post a single tweet. Optional reply or quote for banter/engagement.

    Args:
        text: Tweet text (max 280 chars; 280 for reply/quote).
        reply_to_id: If set, post as a reply to this tweet (rival banter, threads).
        quote_tweet_id: If set, post as a quote tweet (hot takes, clapbacks).

    Returns:
        Tweet id (str) of the new tweet, or None on failure.
    """
    try:
        kwargs = {"text": text}
        if reply_to_id:
            kwargs["in_reply_to_tweet_id"] = str(reply_to_id)
        if quote_tweet_id:
            kwargs["quote_tweet_id"] = str(quote_tweet_id)
        r = client.create_tweet(**kwargs)
        return _tweet_id_from_response(r)
    except Unauthorized as e:
        _raise_401_help(e)


# -----------------------------------------------------------------------------
# Threads (auto-thread generator for IPL/World Cup, viral threads)
# -----------------------------------------------------------------------------


def post_thread(texts, delay_between_sec=1.5):
    """
    Post a thread: first tweet, then each subsequent tweet as a reply to the previous.

    Args:
        texts: List of tweet texts (each max 280 chars). Order is preserved.
        delay_between_sec: Seconds to wait between posts (human-like, avoid rate limits).

    Returns:
        List of tweet ids [root_id, second_id, ...], or empty list if any step failed.
    """
    if not texts:
        return []
    ids = []
    try:
        r = client.create_tweet(text=texts[0])
        first_id = _tweet_id_from_response(r)
        if not first_id:
            return []
        ids.append(first_id)
        reply_to = first_id
        for t in texts[1:]:
            time.sleep(max(0, delay_between_sec))
            r = client.create_tweet(text=t, in_reply_to_tweet_id=str(reply_to))
            next_id = _tweet_id_from_response(r)
            if not next_id:
                return ids  # return what we have
            ids.append(next_id)
            reply_to = next_id
        return ids
    except Unauthorized as e:
        _raise_401_help(e)
    except Exception:
        return ids


# -----------------------------------------------------------------------------
# Reply & quote (rival fan banter, engagement)
# -----------------------------------------------------------------------------


def post_reply(text, reply_to_tweet_id):
    """Post a reply to an existing tweet (e.g. rival fan banter, reply ranking)."""
    return post_tweet(text, reply_to_id=reply_to_tweet_id)


def post_quote(text, quote_tweet_id):
    """Post a quote tweet (hot take, clapback, viral quote)."""
    return post_tweet(text, quote_tweet_id=quote_tweet_id)


# -----------------------------------------------------------------------------
# Tweet context (for reply/banter generation — fetch tweet + author)
# -----------------------------------------------------------------------------


def get_tweet_context(tweet_id):
    """
    Fetch tweet text and author info for reply/banter generation.

    Returns:
        Dict with id, text, author_username, author_id; or None if unavailable.
    """
    try:
        r = client.get_tweet(
            tweet_id,
            tweet_fields=["text"],
            user_fields=["username"],
            expansions=["author_id"],
        )
        if not r.data:
            return None
        t = r.data
        tid = getattr(t, "id", None) or (t.get("id") if isinstance(t, dict) else None)
        text = getattr(t, "text", None) or (t.get("text", "") if isinstance(t, dict) else "")
        author_id = getattr(t, "author_id", None) or (t.get("author_id") if isinstance(t, dict) else None)
        username = None
        if r.includes and "users" in r.includes:
            for u in r.includes["users"]:
                if getattr(u, "id", None) == author_id or (u.get("id") if isinstance(u, dict) else None) == author_id:
                    username = getattr(u, "username", None) or (u.get("username") if isinstance(u, dict) else None)
                    break
        return {"id": str(tid), "text": text or "", "author_id": author_id, "author_username": username or ""}
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Engagement (V6 learning from misses)
# -----------------------------------------------------------------------------


def get_tweet_engagement(tweet_id):
    """
    Fetch like and retweet counts for a tweet (for V6 learning from misses).
    Returns (likes, retweets) or (None, None) if unavailable.
    """
    try:
        r = client.get_tweet(tweet_id, tweet_fields=["public_metrics"])
        if not r.data:
            return None, None
        m = getattr(r.data, "public_metrics", None) or (r.data if isinstance(r.data, dict) else {}).get("public_metrics")
        if m is None:
            return None, None
        likes = getattr(m, "like_count", None) or (m.get("like_count", 0) if isinstance(m, dict) else 0)
        retweets = getattr(m, "retweet_count", None) or (m.get("retweet_count", 0) if isinstance(m, dict) else 0)
        return (int(likes or 0), int(retweets or 0))
    except Exception:
        pass
    return None, None
