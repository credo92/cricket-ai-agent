# Cricket AI Agent

Automated cricket match reaction bot for X (Twitter). Watches match events, detects narrative, generates candidate posts, predicts engagement, and posts the best one with safety checks and optional feedback learning.

## Architecture

```
Match feed / events
        │
        ▼
┌───────────────────┐     ┌────────────────────┐
│  Watcher Agent    │────▶│  Narrative Agent   │
│  watch_match()    │     │  detect_narrative()│
└───────────────────┘     └─────────┬──────────┘
                                    │
                                    ▼
┌───────────────────┐     ┌────────────────────┐
│ Strategist Agent  │────▶│  Decision Agent    │
│  should_post()    │     │  run_decision()    │
└───────────────────┘     │  3 candidates →    │
                          │  predict → best    │
                          └─────────┬──────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
  Safety (duplicate,        X Client              Engagement Agent
  human_delay)              post_tweet()          save_post()
```

**Main loop:** `watch_match` → `detect_narrative` → `should_post` → `run_decision` (3 candidates, engagement prediction, pick best) → safety checks → `post_tweet` → `save_post` (with predicted score for learning).

**Modes:** Run with no arguments for an infinite loop (`run_cycle()` with rate-limit and exception handling). Run with `feedback` to execute the learning job once (backfill actual engagement for past posts).

## Project structure

```
cricket-ai-agent/
├── app/
│   ├── main.py              # Entry: setup_logger(); run_cycle() loop or feedback mode
│   ├── config.py            # Env (OpenAI, X API, delays)
│   ├── safety.py            # human_delay, is_duplicate, remember_post
│   ├── openai_errors.py     # handle_openai_rate_limit
│   ├── x_client.py          # post_tweet, post_thread, post_reply, etc.
│   ├── cricket_events.py    # get_match_event (stub)
│   ├── agents/
│   │   ├── watcher_agent.py
│   │   ├── narrative_agent.py
│   │   ├── strategist_agent.py
│   │   ├── decision_agent.py
│   │   ├── engagement_agent.py
│   │   └── writer_agent.py
│   ├── services/
│   │   ├── engagement_predictor.py
│   │   ├── feedback_learning.py
│   │   ├── match_feed.py
│   │   ├── memory.py
│   │   └── virality.py
│   └── scripts/
│       └── auth_x_oauth.py  # One-time OAuth for X tokens
├── data/                    # Persisted posts, engagement (mounted in Docker)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Setup

### 1. Environment

Copy `.env.example` to `.env` and fill in:

```env
OPENAI_API_KEY=sk-your-openai-key
X_API_KEY=your-consumer-key
X_API_SECRET=your-consumer-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_SECRET=your-access-token-secret
```

Optional: `MATCH_LOOP_SECONDS`, `MIN_POST_DELAY`, `MAX_POST_DELAY` (see `app/config.py`).

### 2. OpenAI API key

1. [platform.openai.com](https://platform.openai.com) → API keys → Create new secret key.
2. Copy the key (starts with `sk-`) into `.env` as `OPENAI_API_KEY`.
3. Set usage limits under Usage and billing if needed. The app uses `gpt-4o-mini`.

### 3. X (Twitter) API credentials

1. [developer.x.com](https://developer.x.com) → sign in, create a project, open **Keys and tokens**.
2. **Consumer keys:** generate and copy API Key → `X_API_KEY`, API Key Secret → `X_API_SECRET`.
3. **Access token:** generate with **Read and write**; copy Access Token → `X_ACCESS_TOKEN`, Access Token Secret → `X_ACCESS_SECRET`.
4. In project **Settings**, set App permissions to **Read and write**.

If the pre-generated token gives 401, use one-time OAuth with ngrok (see `.env.example` comment and `app/scripts/auth_x_oauth.py`).

**Do not commit `.env` or share these values.**

## Run

From project root (so `app` is the package and `data/` is next to `app/`):

```bash
# Main loop: infinite run_cycle() with rate-limit and exception handling
python -m app.main

# One-off: backfill actual engagement for past posts (learning)
python -m app.main feedback
```

Logs are written to `logs/run_YYYYMMDD_HHMMSS.log` and to stdout.

### Docker

```bash
docker compose up --build
```

Uses `Dockerfile` and `docker-compose.yml`; `.env` and `./data` are mounted. Container runs the main loop (infinite `run_cycle()`).

## Flow summary

| Step | Module | Role |
|------|--------|------|
| 1 | `watcher_agent` | Get current match event and state |
| 2 | `narrative_agent` | Detect emotion/narrative from event |
| 3 | `strategist_agent` | Decide whether to post (e.g. skip low-impact) |
| 4 | `decision_agent` | Generate 3 candidates, predict engagement, pick best |
| 5 | `safety` | Duplicate check, human-like delay |
| 6 | `x_client` | Post tweet to X |
| 7 | `engagement_agent` | Save post + predicted score (and later actual engagement via feedback) |

Feedback mode (`python -m app.main feedback`) updates stored posts with actual engagement so the predictor can improve over time.

## Requirements

See `requirements.txt` (e.g. `openai`, `tweepy`, `python-dotenv`, `requests`, `numpy`, etc.).
