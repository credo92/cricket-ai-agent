from cricket_events import (
    get_match_event,
    get_event_and_state,
    is_international_match,
    has_india_team,
    has_women_team,
)


def watch_match():
    """
    Load current matches (from API or file) and return all international matches
    where one of the teams is India (men's only; no women's matches), ordered with
    live in-progress matches first.
    Returns [] if no matches.
    """
    matches = get_match_event()
    if not matches:
        return []

    live = []
    other = []
    for m in matches:
        if (
            m.get("_error")
            or not is_international_match(m)
            or not has_india_team(m)
            or has_women_team(m)
        ):
            continue
        event, state = get_event_and_state(m)
        if event is None:
            continue
        if m.get("matchStarted") and not m.get("matchEnded"):
            live.append((event, state))
        else:
            other.append((event, state))

    return live + other
