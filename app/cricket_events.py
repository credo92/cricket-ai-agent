import json
import os
from pathlib import Path
import requests

CRICAPI_URL = "https://api.cricapi.com/v1/currentMatches"
CRICAPI_KEY = os.getenv("CRICAPI_API_KEY")

# Overs per format for state derivation
OVERS_PER_FORMAT = {"t20": 20, "odi": 50, "test": None}

# International indicators (CricAPI match name/series); domestic e.g. Ranji Trophy lack these
INTERNATIONAL_KEYWORDS = ("ICC", "ACC", "World Cup", "Asia Cup", "T20I", "ODI", " tour of ")


def is_international_match(match):
    """
    Return True if the match is an international event (ICC/ACC events, World Cup,
    Asia Cup, T20I/ODI, or bilateral tours). Excludes domestic leagues (e.g. Ranji Trophy).
    """
    if not match or match.get("_error"):
        return False
    name = (match.get("name") or "").strip()
    for kw in INTERNATIONAL_KEYWORDS:
        if kw in name:
            return True
    return False


def has_india_team(match):
    """
    Return True if one of the teams is India (e.g. "India", "India A Women").
    """
    if not match or match.get("_error"):
        return False
    teams = match.get("teams") or []
    for t in teams:
        if not t:
            continue
        if t == "India" or t.startswith("India "):
            return True
    return False


def has_women_team(match):
    """
    Return True if any team in the match is a women's team (e.g. "India A Women", "Thailand Women").
    """
    if not match or match.get("_error"):
        return False
    teams = match.get("teams") or []
    for t in teams:
        if not t:
            continue
        if " Women" in t or t.endswith("Women"):
            return True
    return False


def _state_from_match(match):
    """
    Build state dict for narrative/strategist from one match dict (current_matches.json shape).
    Provides required_rr and overs_left for limited-overs; narrative_agent uses these.
    """
    state = {
        "required_rr": 0.0,
        "overs_left": 0,
        "match_type": match.get("matchType", ""),
        "match_ended": match.get("matchEnded", False),
        "status": match.get("status", ""),
        "name": match.get("name", ""),
        "teams": match.get("teams", []),
        "score": match.get("score", []),
    }
    score_list = match.get("score") or []
    if not score_list:
        return state

    match_type = (match.get("matchType") or "").lower()
    max_overs = OVERS_PER_FORMAT.get(match_type) if match_type in OVERS_PER_FORMAT else None

    if max_overs and len(score_list) >= 1:
        # Last inning in list is current or just finished
        last = score_list[-1]
        runs = last.get("r", 0)
        overs_bowled = float(last.get("o", 0) or 0)
        state["overs_left"] = max(0, int(max_overs - overs_bowled))

        if len(score_list) >= 2:
            # Second inning: target = first inning runs + 1
            target = (score_list[0].get("r", 0) or 0) + 1
            runs_needed = max(0, target - runs)
            if state["overs_left"] > 0:
                state["required_rr"] = round(runs_needed / state["overs_left"], 2)
            else:
                state["required_rr"] = 0.0

    return state


def _event_summary_from_match(match):
    """Build a short event string for narrative/decision from one match."""
    name = match.get("name", "Match")
    status = match.get("status", "Unknown status")
    score_parts = []
    for s in match.get("score") or []:
        inn = s.get("inning", "")
        r, w, o = s.get("r", ""), s.get("w", ""), s.get("o", "")
        score_parts.append(f"{inn}: {r}/{w} ({o} overs)")
    score_str = " | ".join(score_parts) if score_parts else ""
    return f"{name}. {status}. {score_str}".strip()


def get_match_event():
    """
    Load current matches from current_matches.json (or CricAPI if file missing).
    Returns list of match dicts (each with keys from current_matches.json).
    """
    try:
        response = requests.get(CRICAPI_URL, params={"apikey": CRICAPI_KEY, "offset": 0}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception:
        return []


def get_event_and_state(match):
    """
    From one match dict, return (event_string, state_dict) for pipeline.
    event_string: summary for narrative/decision agents.
    state_dict: required_rr, overs_left, match_type, status, etc. for narrative_agent.
    """
    if not match or match.get("_error"):
        return None, None
    return _event_summary_from_match(match), _state_from_match(match)
