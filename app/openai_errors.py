"""Handle OpenAI API errors (rate limit, quota) with clear messages."""

import sys


def _print_quota_message():
    print(
        "\nOpenAI quota exceeded. Add billing or increase limits at:\n"
        "  https://platform.openai.com/account/billing\n",
        file=sys.stderr,
    )


def handle_openai_rate_limit(exc):
    """
    On 429 rate limit (including insufficient_quota), print a clear message
    and re-raise. Call this from except openai.RateLimitError handlers.
    """
    msg = (getattr(exc, "message", None) or str(exc) or "").lower()
    body = getattr(exc, "body", None) if hasattr(exc, "body") else None
    if isinstance(body, dict):
        err = body.get("error", {}) or {}
        if err.get("type") == "insufficient_quota":
            _print_quota_message()
            raise SystemExit(1)
    # Error payload can also appear in the exception string
    if "insufficient_quota" in msg or "quota" in msg or "insufficient" in msg:
        _print_quota_message()
        raise SystemExit(1)
    # Other rate limit (e.g. RPM): re-raise so caller can retry
    raise
