"""
One-time OAuth 1.0a flow to get X_ACCESS_TOKEN and X_ACCESS_SECRET for .env.

Use when the developer portal's pre-generated token gives 401, or to authorize
a different account. Requires ngrok and the callback URL set in X App info.

Setup:
  1. In X developer console → App info, set:
     Callback URI: https://YOUR-NGROK-URL/callback
     Website URL:  https://YOUR-NGROK-URL
  2. In .env set: X_API_KEY, X_API_SECRET, X_CALLBACK_URL=https://YOUR-NGROK-URL/callback
  3. Run: ngrok http 8765
  4. Run: python -m app.scripts.auth_x_oauth

Then authorize in the browser; the script prints the token and secret for .env.
"""

import os
import sys
import webbrowser
from pathlib import Path

# Load .env from project root
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except Exception:
    pass

import tweepy
from flask import Flask, redirect, request

PORT = 8765
_request_token_store = {}

app = Flask(__name__)


def main():
    api_key = os.getenv("X_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("X_API_SECRET") or os.getenv("API_SECRET")
    callback_url = os.getenv("X_CALLBACK_URL") or os.getenv("CALLBACK_URL")
    if not api_key or not api_secret:
        print("Missing X_API_KEY or X_API_SECRET in .env")
        sys.exit(1)
    if not callback_url or not callback_url.strip().lower().startswith("https://"):
        print("Set X_CALLBACK_URL in .env to your ngrok callback (e.g. https://abc.ngrok-free.app/callback)")
        sys.exit(1)
    callback_url = callback_url.strip()
    if callback_url.endswith("/"):
        callback_url = callback_url.rstrip("/")

    oauth = tweepy.OAuth1UserHandler(
        api_key,
        api_secret,
        callback=callback_url,
    )
    auth_url = oauth.get_authorization_url(signin_with_twitter=True)
    _request_token_store["oauth_token"] = oauth.request_token["oauth_token"]
    _request_token_store["oauth_token_secret"] = oauth.request_token["oauth_token_secret"]
    _request_token_store["api_key"] = api_key
    _request_token_store["api_secret"] = api_secret
    _request_token_store["callback_url"] = callback_url
    _request_token_store["auth_url"] = auth_url

    print("Opening browser to authorize the app. After authorizing you'll be redirected back here.")
    webbrowser.open(auth_url)

    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


@app.route("/")
def index():
    """Redirect to X auth if someone lands on the root (e.g. from a saved link)."""
    auth_url = _request_token_store.get("auth_url")
    return redirect(auth_url if auth_url else "https://developer.x.com")


@app.route("/callback")
def callback():
    verifier = request.args.get("oauth_verifier")
    if not verifier:
        return "<p>Missing oauth_verifier. Try the flow again.</p>", 400
    stored = _request_token_store
    oauth = tweepy.OAuth1UserHandler(
        stored["api_key"],
        stored["api_secret"],
        callback=stored["callback_url"],
    )
    oauth.request_token = {
        "oauth_token": stored["oauth_token"],
        "oauth_token_secret": stored["oauth_token_secret"],
    }
    try:
        access_token, access_token_secret = oauth.get_access_token(verifier)
    except Exception as e:
        return f"<p>Failed to get access token: {e}</p>", 500
    print("\n" + "=" * 60)
    print("Add these to your .env file:")
    print("=" * 60)
    print(f"X_ACCESS_TOKEN={access_token}")
    print(f"X_ACCESS_SECRET={access_token_secret}")
    print("=" * 60)
    print("Then restart the app. You can press Ctrl+C to stop this server.")
    return (
        "<p>Success! Check the terminal for X_ACCESS_TOKEN and X_ACCESS_SECRET to add to .env.</p>"
    )


if __name__ == "__main__":
    # Store auth_url after building oauth in main; we need it for redirect from /
    # For simplicity we don't redirect from / (user already opened auth_url in browser).
    # So / and /callback are enough: user goes to X from our print+webbrowser.open,
    # then X redirects to ngrok/callback -> our /callback.
    main()
